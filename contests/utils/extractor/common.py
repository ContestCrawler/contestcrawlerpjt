from bs4 import BeautifulSoup


CONTENT_SELECTORS = [
    ".board-view",
    ".view-content",
    ".view_cont",
    ".board_view",
    ".bbs_view",
    ".content",
    "#content",
    "article",
    "main",
]


def get_main_content(html):
    # 사이트마다 본문 컨테이너가 다르므로
    # 후보 셀렉터 중 텍스트 길이가 가장 긴 요소를 본문으로 선택한다.
    soup = BeautifulSoup(html, "html.parser")

    best_element = None
    best_length = 0
    for selector in CONTENT_SELECTORS:
        element = soup.select_one(selector)
        if not element:
            continue

        text_length = len(element.get_text(" ", strip=True))
        if text_length > best_length:
            best_element = element
            best_length = text_length

    # 본문을 특정하지 못하면 문서 전체를 fallback으로 사용한다.
    return best_element if best_element else soup
