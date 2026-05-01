from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager


CONTEST_URL = "https://www.data.go.kr/suc/preliminaryRound.do"


@contextmanager
def create_driver():
    options = Options()
    options.add_argument("--window-size=1920, 1080")
    
    # 나중에 추가
    # options.add_argument("--headless=new")
    
    driver = webdriver.Chrome(    
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    
    try:
        yield driver
    
    finally:
        driver.quit()
        
        
def fetch_list_page():
    with create_driver() as driver:
        driver.get(CONTEST_URL)
        return driver.page_source