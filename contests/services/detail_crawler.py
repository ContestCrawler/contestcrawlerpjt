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
    """
    1. 기본적으로 requests 사용하여 빠르게 HTML 요청
    2. requests로 가져오기 힘든 경우 Selenium 활용하여 fallbaock처리 (= 대체 방법 사용)
    """
    
    # 기본은 requests로 빠르게 가져오고,
    # 동적 렌더링이 필요한 경우에만 브라우저 fallback을 사용한다.
    if not prefer_browser:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        
        response.raise_for_status() # HTTP 에러 발생 시 예외 처리
        
        if response.text:
            return response.text

    # 필요한 경우 Selenium 사용
    with create_driver() as driver:
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        return driver.page_source
