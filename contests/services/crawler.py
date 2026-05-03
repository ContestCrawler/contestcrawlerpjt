from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


CONTEST_URL = "https://www.data.go.kr/suc/preliminaryRound.do"


@contextmanager
def create_driver():
    # contextmanager:
    # - with 문으로 사용 가능한 리소스 관리 패턴 제공.
    # - 드라이버 생성/종료를 한 곳에서 관리해 누수 방지.
    options = Options()

    # add_argument():
    # - Chrome 실행 옵션 주입
    # - 화면 크기를 고정해 렌더링 차이를 줄임
    options.add_argument("--window-size=1920, 1080")

    # options.add_argument("--headless=new")
    # - GUI 없는 환경에서 실행할 때 사용

    # Service(ChromeDriverManager().install()):
    # - 실행 가능한 chromedriver 경로를 자동 설치/연결
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )

    # set_page_load_timeout():
    # - 페이지 로딩 무한 대기 방지
    driver.set_page_load_timeout(20)

    try:
        yield driver
    finally:
        # quit():
        # - 브라우저/드라이버 프로세스 완전 종료
        driver.quit()


def fetch_list_page():
    # driver.get(url):
    # - 대상 URL 로딩
    # driver.page_source:
    # - 현재 렌더링된 DOM의 HTML 문자열 반환
    with create_driver() as driver:
        driver.get(CONTEST_URL)
        return driver.page_source
