from bs4 import BeautifulSoup
from django.utils import timezone

from contests.utils.date_parser import parse_period


def clean_text(text):
    # 중복 공백/줄바꿈을 제거해 비교 가능한 텍스트로 정리
    return " ".join(text.split())


def parse_contest_list(html):
    # 목록 페이지에서 카드 단위로 메타데이터를 추출한다.
    # 이미 마감된 항목은 제외한다.
    soup = BeautifulSoup(html, "html.parser")

    today = timezone.localdate()
    wrapper = soup.find("div", id="preliminary-data-list-wrapper")
    cards = wrapper.find_all("li") if wrapper else []

    contests = []
    for card in cards:
        link_tag = card.select_one("a[href]")
        title_tag = card.select_one(".startup-title span")
        period_tag = card.select_one(".float-r")

        bottom_div = card.select_one("a > div:last-child")
        region_tag = bottom_div.select_one("div:first-child span") if bottom_div else None

        detail_url = link_tag.get("href", "") if link_tag else ""
        title = clean_text(title_tag.get_text()) if title_tag else ""
        period = clean_text(period_tag.get_text()) if period_tag else ""
        region = clean_text(region_tag.get_text()) if region_tag else ""

        start_date, end_date = parse_period(period)
        if end_date is None:
            continue
        if end_date < today:
            continue

        contests.append({
            "detail_url": detail_url,
            "title": title,
            "region": region,
            "start_date": start_date,
            "end_date": end_date,
        })

    return contests
