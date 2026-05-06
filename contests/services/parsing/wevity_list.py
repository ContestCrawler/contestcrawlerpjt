from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup


def clean_text(text):
    """
    목록 파싱 중 얻은 텍스트의 연속 공백과 줄바꿈을 단일 공백으로 정리한다.

    의미:
        BeautifulSoup get_text() 결과를 비교와 저장에 안정적인 문자열로 만든다.

    반환값:
        정리된 문자열을 반환한다. None이면 빈 문자열처럼 처리된다.
    """
    return " ".join((text or "").split())


def normalize_wevity_detail_url(url):
    """
    Wevity 상세 URL을 저장 가능한 표준 URL로 정규화한다.

    의미:
        Wevity 상세 페이지 여부를 ix query parameter로 확인하고, 상세 보기용 gbn=viewok 값을 보강한다.

    반환값:
        유효한 Wevity 상세 URL이면 정규화된 URL 문자열을 반환한다.
        Wevity URL이 아니거나 ix가 없으면 빈 문자열을 반환한다.
    """
    parsed = urlparse(url or "")
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    # Error handling:
    # 목록의 광고/외부 링크가 상세 저장 대상으로 들어가지 않도록 빈 문자열로 제외한다.
    if parsed.hostname is None or not parsed.hostname.lower().endswith("wevity.com"):
        return ""
    if not query.get("ix"):
        return ""

    query["gbn"] = "viewok"
    normalized_query = urlencode(query)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", normalized_query, ""))


def get_current_page_number(url):
    """
    Wevity 목록 URL에서 현재 페이지 번호를 읽는다.

    의미:
        다음 페이지 후보를 고를 때 현재 페이지보다 큰 번호만 선택하기 위해 사용한다.

    반환값:
        gp query parameter를 int로 반환한다. 값이 없거나 숫자가 아니면 1을 반환한다.
    """
    query = dict(parse_qsl(urlparse(url or "").query, keep_blank_values=True))
    try:
        return int(query.get("gp", "1"))
    except ValueError:
        # Error handling:
        # gp 값이 깨져 있어도 pagination 비교가 가능하도록 첫 페이지로 취급한다.
        return 1


def parse_wevity_list_items(html, base_url):
    """
    Wevity 목록 HTML에서 공모전 item 목록만 추출한다.

    의미:
        다음 페이지 URL이 필요 없는 호출자를 위한 편의 함수다.

    반환값:
        detail_url, status_text, is_closed를 담은 dict 목록을 반환한다.
    """
    return parse_wevity_list_page(html, base_url)["items"]


def parse_wevity_list_page(html, base_url):
    """
    Wevity 목록 HTML을 item 목록과 다음 페이지 URL로 파싱한다.

    의미:
        목록 컨테이너와 pagination 컨테이너를 찾아 크롤러가 순회할 수 있는 구조로 변환한다.

    반환값:
        dict를 반환한다.
        - items: 상세 URL과 마감 여부를 담은 목록
        - next_page_url: 다음 페이지 URL. 없으면 빈 문자열.
    """
    soup = BeautifulSoup(html, "html.parser")
    list_section = find_wevity_list_section(soup)
    # Error handling:
    # 사이트 구조가 바뀌어 목록 영역을 못 찾으면 빈 결과로 반환해 상위 크롤러가 중단하게 한다.
    if list_section is None:
        return {"items": [], "next_page_url": ""}

    list_container = find_wevity_list_container(list_section)
    # Error handling:
    # 목록 section은 찾았지만 실제 card container가 없으면 파싱 실패로 보고 빈 결과를 반환한다.
    if list_container is None:
        return {"items": [], "next_page_url": ""}

    return {
        "items": build_wevity_list_items(list_container, base_url),
        "next_page_url": find_next_wevity_list_page_url(list_section, base_url),
    }


def find_wevity_list_section(soup):
    """
    Wevity 목록 페이지에서 공모전 목록이 들어 있는 section을 찾는다.

    의미:
        content 영역 안의 main-section 중 ms-list와 pagination이 함께 있는 영역을 우선 선택한다.

    반환값:
        BeautifulSoup node를 반환한다. 적절한 section이 없으면 None을 반환한다.
    """
    content_node = soup.find("div", class_="content")
    # Error handling:
    # 최상위 content가 없으면 Wevity 목록 구조가 아니므로 None을 반환한다.
    if content_node is None:
        return None

    fallback_section = None
    for section in content_node.find_all("div", class_="main-section"):
        list_container = find_wevity_list_container(section)
        if list_container is None:
            continue
        if find_wevity_pagination_container(section) is not None:
            return section
        if fallback_section is None:
            fallback_section = section

    return fallback_section


def find_wevity_list_container(section):
    """
    section 안에서 실제 공모전 카드 목록 컨테이너(ms-list)를 찾는다.

    의미:
        Wevity 목록 item들이 들어 있는 div.ms-list를 찾는 구조 탐색 helper다.

    반환값:
        div.ms-list node를 반환한다. section이 없거나 컨테이너가 없으면 None을 반환한다.
    """
    if section is None:
        return None

    for child in section.find_all("div", recursive=False):
        if "ms-list" in child.get("class", []):
            return child

    return section.find("div", class_="ms-list")


def find_wevity_pagination_container(section):
    """
    section 안에서 pagination 컨테이너(list-navi)를 찾는다.

    의미:
        다음 페이지 URL 후보를 추출할 영역을 찾는다.

    반환값:
        div.list-navi node를 반환한다. section이 없거나 pagination이 없으면 None을 반환한다.
    """
    if section is None:
        return None

    for child in section.find_all("div", recursive=False):
        if "list-navi" in child.get("class", []):
            return child

    return section.find("div", class_="list-navi")


def build_wevity_list_items(list_container, base_url):
    """
    Wevity 목록 컨테이너에서 중복 없는 공모전 item dict 목록을 만든다.

    의미:
        각 카드에서 상세 URL과 상태 텍스트를 뽑고, 같은 상세 URL은 한 번만 포함한다.

    반환값:
        detail_url, status_text, is_closed를 담은 dict 목록을 반환한다.
    """
    items = []
    seen_urls = set()

    for item_node in find_wevity_contest_item_nodes(list_container):
        detail_url = extract_wevity_detail_url(item_node, base_url)
        # Error handling:
        # 상세 URL을 만들 수 없거나 이미 본 URL이면 저장 대상에서 제외한다.
        if not detail_url or detail_url in seen_urls:
            continue

        status_text = extract_wevity_status_text(item_node)
        seen_urls.add(detail_url)
        items.append(
            {
                "detail_url": detail_url,
                "status_text": status_text,
                "is_closed": is_wevity_closed_status(status_text),
            }
        )

    return items


def find_wevity_contest_item_nodes(list_container):
    """
    Wevity 목록 컨테이너에서 실제 공모전 카드 li node만 찾는다.

    의미:
        목록 안에는 보조/광고성 li가 섞일 수 있으므로 item 판별 함수를 거쳐 필터링한다.

    반환값:
        공모전 카드로 판단되는 li node 목록을 반환한다.
    """
    if list_container is None:
        return []

    list_node = list_container.find("ul", class_="list")
    # Error handling:
    # 예상 목록 ul이 없으면 item이 없는 것으로 처리한다.
    if list_node is None:
        return []

    return [
        item_node
        for item_node in list_node.find_all("li", recursive=False)
        if is_wevity_contest_item_node(item_node)
    ]


def is_wevity_contest_item_node(item_node):
    """
    li node가 실제 Wevity 공모전 카드인지 판단한다.

    의미:
        현재 Wevity 구조에서 실제 카드 li는 class가 없거나 bg 하나만 가진다는 규칙을 사용한다.

    반환값:
        실제 공모전 카드로 볼 수 있으면 True, 아니면 False를 반환한다.
    """
    item_classes = item_node.get("class", [])
    return not item_classes or item_classes == ["bg"]


def extract_wevity_detail_url(item_node, base_url):
    """
    Wevity 목록 item에서 상세 URL을 추출하고 정규화한다.

    의미:
        상대 href를 base_url 기준 절대 URL로 바꾼 뒤 Wevity 상세 URL 규칙에 맞게 정리한다.

    반환값:
        정규화된 상세 URL 문자열을 반환한다. 링크가 없거나 유효하지 않으면 빈 문자열을 반환한다.
    """
    link = item_node.select_one("a[href]")
    if link is None:
        return ""

    href = clean_text(link.get("href", ""))
    return normalize_wevity_detail_url(urljoin(base_url, href))


def extract_wevity_status_text(item_node):
    """
    Wevity 목록 item에서 접수 상태 텍스트를 추출한다.

    의미:
        마감 여부를 판단하기 위해 dday 영역의 표시 텍스트를 가져온다.

    반환값:
        상태 텍스트 문자열을 반환한다. 찾지 못하면 빈 문자열을 반환한다.
    """
    status_node = item_node.select_one("span.dday.ing")
    if status_node is not None:
        return clean_text(status_node.get_text(" ", strip=True))

    status_node = item_node.select_one(".dday")
    if status_node is not None:
        return clean_text(status_node.get_text(" ", strip=True))

    return ""


def is_wevity_closed_status(status_text):
    """
    상태 텍스트가 마감 상태인지 판단한다.

    의미:
        목록이 최신순이라고 가정하고, 마감 항목을 만나는 순간 크롤링 중단 여부를 결정한다.

    반환값:
        상태 텍스트가 "마감"이면 True, 아니면 False를 반환한다.
    """
    return clean_text(status_text) == "마감"


def find_next_wevity_list_page_url(list_section, base_url):
    """
    Wevity pagination에서 현재 페이지보다 뒤의 가장 가까운 페이지 URL을 찾는다.

    의미:
        이전 페이지나 현재 페이지 링크를 잘못 따라가 무한 루프가 생기지 않도록
        페이지 번호가 증가하는 후보만 다음 페이지로 선택한다.

    반환값:
        다음 페이지 URL 문자열을 반환한다. 후보가 없으면 빈 문자열을 반환한다.
    """
    pagination = find_wevity_pagination_container(list_section)
    # Error handling:
    # pagination이 없으면 더 진행할 페이지가 없다고 판단한다.
    if pagination is None:
        return ""

    current_page = get_current_page_number(base_url)
    next_page_candidates = []
    for link in pagination.select("a[href]"):
        href = clean_text(link.get("href", ""))
        if not href:
            continue

        target_url = urljoin(base_url, href)
        target_page = get_current_page_number(target_url)
        if target_page > current_page:
            next_page_candidates.append((target_page, target_url))

    if not next_page_candidates:
        return ""

    next_page_candidates.sort(key=lambda item: item[0])
    return next_page_candidates[0][1]
