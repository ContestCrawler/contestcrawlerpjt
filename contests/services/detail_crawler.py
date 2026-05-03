import requests

from contests.services.crawler import create_driver


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch_detail_page(url, prefer_browser=False, timeout=20):
    # requests.get():
    # - HTTP 요청으로 HTML을 빠르게 가져옴
    # - headers에 User-Agent를 넣어 일부 사이트의 봇 차단을 줄임
    #
    # response.raise_for_status():
    # - 4xx/5xx 응답을 즉시 예외로 올려 상위에서 에러 처리 가능하게 함
    if not prefer_browser:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
        if response.text:
            return response.text

    # Selenium fallback:
    # - JS 렌더링 의존 페이지는 requests HTML만으로 정보가 부족할 수 있어 브라우저 경로 제공
    with create_driver() as driver:
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        return driver.page_source
