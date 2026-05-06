import requests

from contests.services.crawling.browser import create_chrome_driver


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch_page_with_browser(url):
    """
    주어진 URL을 Selenium 브라우저로 열고 렌더링된 HTML을 가져온다.

    의미:
        requests만으로는 JavaScript 실행 결과를 얻기 어려운 페이지를 처리한다.

    반환값:
        브라우저가 현재 페이지에서 가진 page_source 문자열을 반환한다.
    """
    with create_chrome_driver() as driver:
        driver.get(url)
        return driver.page_source


def fetch_detail_html(url, prefer_browser=False, timeout=20):
    """
    상세 페이지 HTML을 가져온다.

    의미:
        기본적으로 빠른 requests를 먼저 사용하고, 브라우저가 꼭 필요하거나
        requests 결과가 비어 있으면 Selenium 브라우저 경로로 fallback한다.

    반환값:
        상세 페이지의 HTML 문자열을 반환한다.

    예외:
        requests 응답이 4xx/5xx이면 raise_for_status()가 HTTPError를 발생시킨다.
        브라우저 실행/페이지 로딩 실패는 Selenium 계열 예외로 상위 호출자에게 전달된다.
    """
    if not prefer_browser:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        # Error handling:
        # 실패한 HTTP 응답을 빈 HTML처럼 다루지 않고 상위 계층에서 명확히 처리하게 한다.
        response.raise_for_status()
        if response.text:
            return response.text

    # Error handling:
    # requests로 충분한 HTML을 얻지 못한 경우를 대비한 브라우저 fallback 경로다.
    with create_chrome_driver() as driver:
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        return driver.page_source


def fetch_wevity_list_html(list_url):
    """
    Wevity 목록 페이지 HTML을 브라우저로 가져온다.

    의미:
        목록 페이지는 렌더링 상태에 의존할 수 있으므로 Selenium fetch 경로를 고정해서 쓴다.

    반환값:
        Wevity 목록 페이지의 렌더링된 HTML 문자열을 반환한다.
    """
    return fetch_page_with_browser(list_url)
