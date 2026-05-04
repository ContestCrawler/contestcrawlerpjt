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
    """
    범용 상세 페이지에서 "본문으로 보이는 영역"을 추정한다.
    
    위비티처럼 구조가 확실한 사이트는 전용 파서에서 .article을 직접 선택한다.
    하지만 공공데이터포털을 통해 들어온 외부 상세 사이트는 HTML 구조가 제각각이라
    .content, article, main 같은 흔한 본문 컨테이너 후보 중 하나를 골라야 한다.
    => 그래서, 여러 본문 후보 중에서 텍스트가 가장 많은 영역을 고른다.
    """
    
    soup = BeautifulSoup(html, "html.parser")

    best_element = None
    best_text_length = 0

    for selector in CONTENT_SELECTORS:
        element = soup.select_one(selector)
        if not element:
            continue

        # 후보가 여러 개 있을 때는 텍스트가 가장 많은 영역을 본문에 가깝다고 본다.
        # 예를 들어 .content가 짧은 안내 영역이고 article이 긴 공모전 설명이면
        # article을 선택해야 하므로 현재까지의 최대 텍스트 길이를 기억한다.
        text_length = len(element.get_text(" ", strip=True))

        if text_length > best_text_length:
            best_element = element
            best_text_length = text_length

    # 본문 후보 selector가 하나도 맞지 않으면 전체 문서를 fallback으로 사용한다.
    # 정확도는 떨어질 수 있지만, prefill 자체가 빈 값으로 끝나는 것보다는 낫다.
    return best_element if best_element else soup
