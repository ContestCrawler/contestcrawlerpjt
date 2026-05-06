from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup


def clean_text(text):
    return " ".join((text or "").split())


def normalize_wevity_detail_url(url):
    parsed = urlparse(url or "")
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    if parsed.hostname is None or not parsed.hostname.lower().endswith("wevity.com"):
        return ""
    if not query.get("ix"):
        return ""

    query["gbn"] = "viewok"
    normalized_query = urlencode(query)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", normalized_query, ""))


def get_current_page_number(url):
    query = dict(parse_qsl(urlparse(url or "").query, keep_blank_values=True))
    try:
        return int(query.get("gp", "1"))
    except ValueError:
        return 1


def parse_contest_list(html, base_url):
    return parse_contest_list_page(html, base_url)["items"]


def parse_contest_list_page(html, base_url):
    # 리스트 페이지는 "어떤 상세 URL을 수집 대상으로 볼지"를 판단하는 용도로만 사용한다.
    # 실제 저장에 필요한 제목, 설명, 기간 등의 메타데이터는 상세 페이지가 기준이므로
    # 여기서는 아이템 판별에 필요한 최소 정보만 추출한다.
    soup = BeautifulSoup(html, "html.parser")
    list_section = find_list_section(soup)
    if list_section is None:
        return {"items": [], "next_page_url": ""}

    ms_list = find_ms_list_node(list_section)
    if ms_list is None:
        return {"items": [], "next_page_url": ""}

    return {
        "items": build_contest_items(ms_list, base_url),
        "next_page_url": find_next_page_url(list_section, base_url),
    }


def find_list_section(soup):
    content_node = soup.find("div", class_="content")
    if content_node is None:
        return None

    fallback_section = None
    for section in content_node.find_all("div", class_="main-section"):
        ms_list = find_ms_list_node(section)
        if ms_list is None:
            continue
        # 같은 main-section 안에 목록(ms-list)과 페이지네이션(list-navi)이 함께 있는
        # 구간을 우선적으로 사용한다. 그래야 페이지 내의 다른 부가 섹션과 섞이지 않는다.
        if find_list_navi_node(section) is not None:
            return section
        if fallback_section is None:
            fallback_section = section

    return fallback_section


def find_ms_list_node(section):
    if section is None:
        return None

    for child in section.find_all("div", recursive=False):
        if "ms-list" in child.get("class", []):
            return child

    return section.find("div", class_="ms-list")


def find_list_navi_node(section):
    if section is None:
        return None

    for child in section.find_all("div", recursive=False):
        if "list-navi" in child.get("class", []):
            return child

    return section.find("div", class_="list-navi")


def build_contest_items(ms_list, base_url):
    items = []
    seen_urls = set()

    for item_node in find_contest_item_nodes(ms_list):
        detail_url = extract_detail_url(item_node, base_url)
        if not detail_url or detail_url in seen_urls:
            continue

        status_text = extract_status_text(item_node)
        seen_urls.add(detail_url)
        items.append(
            {
                "detail_url": detail_url,
                "status_text": status_text,
                "is_closed": is_closed_status_text(status_text),
            }
        )

    return items


def find_contest_item_nodes(ms_list):
    if ms_list is None:
        return []

    list_node = ms_list.find("ul", class_="list")
    if list_node is None:
        return []

    item_nodes = []
    for item_node in list_node.find_all("li", recursive=False):
        # 위비티 목록에는 실제 공모전 행 외에도 top 같은 보조 행이 섞여 있다.
        # 따라서 현재 구조에서 공모전으로 볼 수 있는 li만 다음 단계로 넘긴다.
        if is_contest_item_node(item_node):
            item_nodes.append(item_node)

    return item_nodes


def is_contest_item_node(item_node):
    item_classes = item_node.get("class", [])
    # 현재 위비티 목록에서 실제 공모전 행은 클래스가 없거나, 줄무늬 배경용 bg 클래스를 가진다.
    # 그 외 top 같은 클래스는 목록 보조 행으로 보고 제외한다.
    return not item_classes or item_classes == ["bg"]


def extract_detail_url(item_node, base_url):
    link = item_node.select_one("a[href]")
    if link is None:
        return ""

    href = clean_text(link.get("href", ""))
    return normalize_wevity_detail_url(urljoin(base_url, href))


def extract_status_text(item_node):
    # 목록 행에서 현재현황은 span.dday.ing를 가장 우선적으로 본다.
    # 사용자가 종료 조건을 이 영역의 "마감" 텍스트로 판단하기로 했기 때문이다.
    status_node = item_node.select_one("span.dday.ing")
    if status_node is not None:
        return clean_text(status_node.get_text(" ", strip=True))

    # 마크업이 약간 달라질 가능성을 고려해서 dday 전체도 한 번 더 확인한다.
    status_node = item_node.select_one(".dday")
    if status_node is not None:
        return clean_text(status_node.get_text(" ", strip=True))

    return ""


def is_closed_status_text(status_text):
    # 종료 조건은 의도적으로 엄격하게 둔다.
    # 현재현황 텍스트가 정확히 "마감"일 때만 수집 종료 대상으로 본다.
    return clean_text(status_text) == "마감"


def find_next_page_url(list_section, base_url):
    list_navi = find_list_navi_node(list_section)
    if list_navi is None:
        return ""

    current_page = get_current_page_number(base_url)
    next_page_candidates = []
    for link in list_navi.select("a[href]"):
        href = clean_text(link.get("href", ""))
        if not href:
            continue

        target_url = urljoin(base_url, href)
        target_page = get_current_page_number(target_url)
        # 현재 페이지보다 뒤에 있는 번호만 다음 후보로 본다.
        # 이렇게 해야 잘못된 링크 때문에 이전 페이지로 되돌아가거나 반복 루프에 빠지지 않는다.
        if target_page > current_page:
            next_page_candidates.append((target_page, target_url))

    if not next_page_candidates:
        return ""

    next_page_candidates.sort(key=lambda item: item[0])
    return next_page_candidates[0][1]
