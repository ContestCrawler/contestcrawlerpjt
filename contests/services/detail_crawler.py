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
    # 상세 페이지는 가능하면 requests로 먼저 가져온다.
    # 이 경로가 더 빠르고, 브라우저를 띄우지 않아도 되는 경우가 많기 때문이다.
    if not prefer_browser:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        # 4xx/5xx 응답은 여기서 바로 예외로 올려서 상위에서 처리하게 한다.
        response.raise_for_status()
        if response.text:
            return response.text

    # requests 결과만으로 HTML이 부족하거나 JS 렌더링이 필요한 경우를 대비해
    # Selenium 브라우저 경로를 fallback으로 둔다.
    with create_driver() as driver:
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        return driver.page_source
