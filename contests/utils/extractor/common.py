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
    # BeautifulSoup():
    # - HTML 문자열을 트리 객체로 변환해 selector 탐색 가능하게 만든다.
    soup = BeautifulSoup(html, "html.parser")

    best_element = None
    best_length = 0

    for selector in CONTENT_SELECTORS:
        # select_one():
        # - CSS selector에 맞는 첫 노드 1개만 반환.
        # - 본문 컨테이너는 보통 하나라서 select()보다 효율적.
        element = soup.select_one(selector)
        if not element:
            continue

        # get_text(" ", strip=True):
        # - 요소 하위 텍스트를 공백으로 합치고 앞뒤 공백 제거.
        # len()으로 텍스트량을 비교해 "가장 본문에 가까운 영역"을 선택한다.
        text_length = len(element.get_text(" ", strip=True))

        if text_length > best_length:
            best_element = element
            best_length = text_length

    # selector 후보가 하나도 안 맞으면 문서 전체를 fallback으로 반환.
    return best_element if best_element else soup
