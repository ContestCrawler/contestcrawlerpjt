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
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", urlencode(query), ""))


def get_current_page_number(url):
    query = dict(parse_qsl(urlparse(url or "").query, keep_blank_values=True))
    try:
        return int(query.get("gp", "1"))
    except ValueError:
        return 1


def parse_contest_list(html, base_url):
    return parse_contest_list_page(html, base_url)["items"]


def parse_contest_list_page(html, base_url):
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
    list_node = ms_list.find("ul", class_="list")
    if list_node is None:
        return []

    items = []
    seen_urls = set()
    for item_node in list_node.find_all("li", recursive=False):
        item_classes = item_node.get("class", [])
        if item_classes and item_classes != ["bg"]:
            continue

        link = item_node.select_one("a[href]")
        if link is None:
            continue

        detail_url = normalize_wevity_detail_url(urljoin(base_url, clean_text(link.get("href", ""))))
        if not detail_url or detail_url in seen_urls:
            continue

        status_node = item_node.select_one("span.dday.ing") or item_node.select_one(".dday")
        status_text = clean_text(status_node.get_text(" ", strip=True)) if status_node is not None else ""
        seen_urls.add(detail_url)
        items.append(
            {
                "detail_url": detail_url,
                "status_text": status_text,
                "is_closed": status_text == "마감",
            }
        )

    return items


def find_next_page_url(list_section, base_url):
    list_navi = find_list_navi_node(list_section)
    if list_navi is None:
        return ""

    current_page = get_current_page_number(base_url)
    candidates = []
    for link in list_navi.select("a[href]"):
        href = clean_text(link.get("href", ""))
        if not href:
            continue
        target_url = urljoin(base_url, href)
        target_page = get_current_page_number(target_url)
        if target_page > current_page:
            candidates.append((target_page, target_url))

    if not candidates:
        return ""

    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]
