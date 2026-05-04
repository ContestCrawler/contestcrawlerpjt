from bs4 import BeautifulSoup
from django.utils import timezone

from contests.utils.date_parser import parse_period


def clean_text(text):
    # split()/join()으로 공백 정규화
    return " ".join(text.split())


def parse_contest_list(html):
    # BeautifulSoup 파싱 객체 생성
    soup = BeautifulSoup(html, "html.parser")

    # timezone.localdate():
    # - 서버 로컬 타임존 기준 오늘 날짜(date) 반환
    # - 마감 여부 비교에 사용
    today = timezone.localdate()

    # soup.find():
    # - id로 특정 래퍼 1개 탐색
    wrapper = soup.find("div", id="preliminary-data-list-wrapper")

    # wrapper.find_all("li"):
    # - 카드 컨테이너에서 목록 아이템 전부 수집
    cards = wrapper.find_all("li") if wrapper else []

    contests = []
    for card in cards:
        # select_one():
        # - CSS selector로 카드 내부 요소를 안정적으로 탐색
        link_tag = card.select_one("a[href]")
        title_tag = card.select_one(".startup-title span")
        period_tag = card.select_one(".float-r")

        bottom_div = card.select_one("a > div:last-child")
        region_tag = bottom_div.select_one("div:first-child span") if bottom_div else None

        # 태그가 없을 수 있어 삼항식으로 안전 처리
        detail_url = link_tag.get("href", "") if link_tag else ""
        title = clean_text(title_tag.get_text()) if title_tag else ""
        period = clean_text(period_tag.get_text()) if period_tag else ""
        host_region = clean_text(region_tag.get_text()) if region_tag else ""

        # parse_period():
        # - "YYYY-MM-DD ~ YYYY-MM-DD"를 date 2개로 변환
        start_date, end_date = parse_period(period)
        if end_date is None:
            continue
        if end_date < today:
            continue

        contests.append({
            "detail_url": detail_url,
            "title": title,
            "host_region": host_region,
            "start_date": start_date,
            "end_date": end_date,
        })

    return contests
