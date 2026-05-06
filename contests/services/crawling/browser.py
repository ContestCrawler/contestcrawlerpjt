from contextlib import contextmanager


@contextmanager
def create_chrome_driver():
    """
    Selenium Chrome WebDriver를 생성하고 사용이 끝나면 자동으로 종료한다.

    의미:
        JavaScript 렌더링이 필요한 목록/상세 페이지를 브라우저로 가져올 때 쓰는
        가장 낮은 단계의 브라우저 실행 도구다.

    반환값:
        context manager 안에서 Selenium WebDriver 인스턴스를 yield한다.
        with 블록이 끝나면 반환값은 없고, driver.quit()으로 브라우저를 닫는다.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

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
        # Error handling:
        # with 블록 안에서 예외가 발생해도 브라우저 프로세스가 남지 않도록 항상 종료한다.
        driver.quit()
