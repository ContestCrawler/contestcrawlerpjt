from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


CONTEST_URL = "https://www.data.go.kr/suc/preliminaryRound.do"


@contextmanager
def create_driver():
    # Selenium WebDriver 공통 생성기.
    # with 블록이 끝나면 자동으로 quit 하여 리소스 누수를 막는다.
    options = Options()
    options.add_argument("--window-size=1920, 1080")

    # 필요 시 headless 모드 사용
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    driver.set_page_load_timeout(20)

    try:
        yield driver
    finally:
        driver.quit()


def fetch_list_page():
    # 공모전 목록 페이지의 렌더링된 HTML을 반환한다.
    with create_driver() as driver:
        driver.get(CONTEST_URL)
        return driver.page_source
