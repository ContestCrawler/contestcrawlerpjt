from contests.services.crawling.fetchers import fetch_wevity_list_html
from contests.services.parsing.wevity_list import parse_wevity_list_page as parse_wevity_list_html
from contests.services.prefilling.url_rules import is_wevity_detail_url, is_wevity_list_url


DEFAULT_WEVITY_LIST_URL = "https://www.wevity.com/?c=find&s=1&gub=1&cidx=20"


def crawl_wevity_contests(source_urls):
    """
    여러 Wevity 상세 URL을 순서대로 저장한다.

    의미:
        이미 수집 대상 상세 URL 목록을 알고 있을 때 사용하는 batch 진입점이다.

    반환값:
        명시적인 반환값은 없다. 각 URL은 Contest 및 자산 레코드로 저장된다.
    """
    for source_url in source_urls:
        save_wevity_contest_from_detail_url(source_url)


def crawl_wevity_list(list_url):
    """
    Wevity 목록 URL에서 시작해 최신 공모전을 페이지 단위로 수집한다.

    의미:
        목록 페이지를 순회하면서 마감 공모전을 처음 만나면 최신 구간이 끝났다고 보고
        수집을 중단한다. 이미 방문한 페이지는 재방문하지 않는다.

    반환값:
        명시적인 반환값은 없다. 수집한 상세 페이지는 DB에 저장된다.

    예외:
        목록 URL이 비어 있거나 Wevity 목록 URL이 아니면 ValueError가 발생한다.
        상세 저장 과정의 예외는 상위 호출자에게 전달된다.
    """
    next_page_url = validate_wevity_list_url(list_url)
    visited_pages = set()

    while should_visit_page(next_page_url, visited_pages):
        visited_pages.add(next_page_url)
        page_result = crawl_wevity_list_once(next_page_url)

        if page_result["should_stop"]:
            return

        next_page_url = page_result["next_page_url"]


def crawl_wevity_list_once(list_url):
    """
    Wevity 목록 한 페이지를 처리한다.

    의미:
        현재 페이지의 공모전 카드들을 순서대로 확인하고, 열린 공모전은 상세 저장까지 수행한다.
        마감 항목을 만나거나 목록 파싱 결과가 비어 있으면 전체 크롤링을 멈추도록 신호를 만든다.

    반환값:
        dict를 반환한다.
        - next_page_url: 다음 목록 페이지 URL. 중단해야 하면 빈 문자열.
        - should_stop: 상위 반복 크롤링을 중단해야 하면 True.
    """
    parsed_page = parse_wevity_list_url(list_url)
    items = parsed_page["items"]

    # Error handling:
    # 목록 구조가 바뀌었거나 파싱에 실패해 항목이 없으면 다음 페이지로 무리하게 진행하지 않는다.
    if not items:
        return {"next_page_url": "", "should_stop": True}

    for item in items:
        if item["is_closed"]:
            return {"next_page_url": "", "should_stop": True}

        save_wevity_contest_from_detail_url(item["detail_url"])

    return {
        "next_page_url": parsed_page["next_page_url"],
        "should_stop": False,
    }


def parse_wevity_list_url(list_url):
    """
    Wevity 목록 URL을 HTML로 가져온 뒤 목록 파서 결과로 변환한다.

    의미:
        crawling 계층과 parsing 계층을 연결하는 작은 어댑터 역할을 한다.

    반환값:
        parse_wevity_list_html()의 결과 dict를 반환한다.
        - items: 상세 URL, 상태 텍스트, 마감 여부를 담은 목록
        - next_page_url: 다음 페이지 URL
    """
    list_html = fetch_wevity_list_html(list_url)
    return parse_wevity_list_html(list_html, list_url)


def save_wevity_contest_from_detail_url(source_url):
    """
    Wevity 상세 URL 하나를 prefill 데이터로 변환하고 Contest로 저장한다.

    의미:
        목록 크롤러가 발견한 상세 URL을 실제 DB 저장까지 연결하는 저장 진입점이다.

    반환값:
        명시적인 반환값은 없다. 내부에서 Contest와 이미지/첨부파일 레코드를 생성한다.

    예외:
        Wevity 상세 URL이 아니면 ValueError를 발생시킨다.
        상세 HTML fetch, 파싱, DB 저장 실패는 상위 호출자에게 전달된다.
    """
    from contests.services.persistence.contest_assets import create_contest_with_assets
    from contests.services.prefilling.builder import load_contest_prefill

    # Error handling:
    # 목록 URL이나 다른 사이트 URL이 저장 경로로 들어오는 실수를 초기에 차단한다.
    if not is_wevity_detail_url(source_url):
        raise ValueError(f"Only Wevity detail URLs are supported: {source_url}")

    prefill_data = load_contest_prefill(source_url)
    create_contest_with_assets(prefill_data)


def validate_wevity_list_url(list_url, is_list_url_checker=None):
    """
    입력값이 Wevity 목록 URL인지 검증하고 앞뒤 공백을 제거한 URL을 반환한다.

    의미:
        view나 command에서 받은 사용자 입력을 크롤러가 처리 가능한 형태로 보정한다.

    반환값:
        공백이 제거된 Wevity 목록 URL 문자열을 반환한다.

    예외:
        URL이 비어 있거나 검사 함수가 False를 반환하면 ValueError를 발생시킨다.
    """
    is_list_url_checker = is_list_url_checker or is_wevity_list_url
    normalized_list_url = (list_url or "").strip()

    # Error handling:
    # 비어 있는 입력과 상세 URL 입력을 같은 사용자 메시지로 막아 크롤러 오작동을 피한다.
    if not normalized_list_url:
        raise ValueError("Please enter a Wevity list URL.")
    if not is_list_url_checker(normalized_list_url):
        raise ValueError("Please enter a Wevity list URL.")

    return normalized_list_url


def should_visit_page(next_page_url, visited_pages):
    """
    다음 페이지 URL을 방문해도 되는지 판단한다.

    의미:
        빈 URL과 이미 방문한 URL을 제외해 무한 루프를 막는다.

    반환값:
        방문할 URL이 있고 아직 방문하지 않았으면 True, 아니면 False를 반환한다.
    """
    return bool(next_page_url) and next_page_url not in visited_pages


def crawl_latest_wevity_contests(list_url=DEFAULT_WEVITY_LIST_URL):
    """
    기본 Wevity 목록 URL을 기준으로 최신 공모전 수집을 시작한다.

    의미:
        스케줄러나 관리 명령에서 인자 없이 호출하기 좋은 기본 크롤링 진입점이다.

    반환값:
        crawl_wevity_list()를 실행하며 명시적인 반환값은 없다.
    """
    crawl_wevity_list(list_url)
