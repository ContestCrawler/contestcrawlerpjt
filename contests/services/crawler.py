from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from contests.services.parser import parse_contest_list_page


DEFAULT_WEVITY_LIST_URL = "https://www.wevity.com/?c=find&s=1&gub=1&cidx=20"


@contextmanager
def create_driver():
    options = Options()
    options.add_argument("--window-size=1920, 1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    driver.set_page_load_timeout(20)

    try:
        yield driver
    finally:
        driver.quit()


def fetch_list_page(list_url):
    with create_driver() as driver:
        driver.get(list_url)
        return driver.page_source


def crawl_wevity_contests(source_urls):
    for source_url in source_urls:
        save_wevity_detail_url(source_url)


def crawl_wevity_list_page(list_url):
    from contests.services.prefill import is_wevity_list_url

    # 입력 URL 검증
    normalized_list_url = validate_wevity_list_url(list_url, is_wevity_list_url)
    next_page_url = normalized_list_url
    visited_pages = set()

    # 페이지 반복의 시작
    # 다음 페이지 URL있고 아직 방문하지 않은 페이지라면 계속 반복
    while should_visit_page(next_page_url, visited_pages):
        visited_pages.add(next_page_url) # 현재 페이지 방문 처리
        
        # 한 페이지에 대한 처리 로직 시작
        page_result = crawl_wevity_list_page_once(next_page_url) 

        if page_result["should_stop"]:
            return

        next_page_url = page_result["next_page_url"]


def crawl_wevity_list_page_once(list_url):
    # 한 페이지를 처리할 때의 규칙은 단순하다.
    # 1. 현재 페이지의 공모전 아이템들을 순서대로 본다.
    # 2. "마감"이 아닌 항목은 상세 페이지로 들어가 저장한다.
    # 3. 처음으로 "마감"을 만나면 최신순이라는 전제하에 즉시 전체 수집을 멈춘다.
    parsed_page = parse_wevity_list_page(list_url)
    items = parsed_page["items"]

    if not items:
        # 파싱 결과가 비어 있으면 구조가 바뀌었거나 예상과 다른 페이지일 수 있다.
        # 이 경우 억지로 다음 페이지로 넘기지 말고 여기서 안전하게 중단한다.
        return {"next_page_url": "", "should_stop": True}

    for item in items:
        if item["is_closed"]:
            # 목록이 최신순으로 정렬되어 있다고 가정한다.
            # 따라서 여기서 "마감"을 만났다면 같은 페이지 뒤쪽과 다음 페이지들은
            # 더 이상 수집 대상이 아니라고 보고 즉시 종료한다.
            return {"next_page_url": "", "should_stop": True}

        save_wevity_detail_url(item["detail_url"])

    return {
        "next_page_url": parsed_page["next_page_url"],
        "should_stop": False,
    }


def parse_wevity_list_page(list_url):
    list_html = fetch_list_page(list_url)
    return parse_contest_list_page(list_html, list_url)


def save_wevity_detail_url(source_url):
    from contests.services.contest_writer import create_contest_with_assets
    from contests.services.prefill import is_wevity_detail_url, load_prefill_data

    if not is_wevity_detail_url(source_url):
        raise ValueError(f"Only Wevity detail URLs are supported: {source_url}")

    # 리스트 페이지에서는 수집 대상을 고르는 판단만 하고,
    # 실제 저장용 데이터는 반드시 상세 페이지에 들어가서 가져오도록 분리한다.
    prefill_data = load_prefill_data(source_url)
    create_contest_with_assets(prefill_data)


def validate_wevity_list_url(list_url, is_wevity_list_url):
    normalized_list_url = (list_url or "").strip()
    
    if not normalized_list_url:
        raise ValueError("Please enter a Wevity list URL.")
    if not is_wevity_list_url(normalized_list_url):
        raise ValueError("Please enter a Wevity list URL.")
    
    return normalized_list_url


def should_visit_page(next_page_url, visited_pages):
    # 방문한 페이지를 기억해 두면 잘못된 페이지네이션 링크가 현재 페이지를 다시 가리키거나
    # 몇 개 페이지 사이를 순환하더라도 무한 반복을 막을 수 있다.
    return bool(next_page_url) and next_page_url not in visited_pages


def crawl_latest_wevity_contests(list_url=DEFAULT_WEVITY_LIST_URL):
    crawl_wevity_list_page(list_url)
