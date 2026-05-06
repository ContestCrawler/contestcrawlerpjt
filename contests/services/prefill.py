from urllib.parse import parse_qs, urlparse

from contests.services.detail_crawler import fetch_detail_page
from contests.services.prefill_detail_parser import parse_detail_fields


def get_hostname(url):
    hostname = urlparse(url or "").hostname or ""
    return hostname.lower()


def get_query_params(url):
    return parse_qs(urlparse(url or "").query)


def is_wevity_url(url):
    return get_hostname(url).endswith("wevity.com")


def is_wevity_detail_url(url):
    # 위비티 상세 페이지는 쿼리스트링에 ix 값이 포함되어 있다.
    # 이 값이 있어야 실제 공모전 상세 페이지로 들어갈 수 있다.
    return is_wevity_url(url) and bool(get_query_params(url).get("ix"))


def is_wevity_list_url(url):
    # 현재 흐름에서 리스트 URL은 "위비티 도메인이면서 상세 URL은 아닌 경우"로 본다.
    # 사용자가 분야별 목록 페이지를 넣는지 먼저 구분하기 위한 헬퍼다.
    return is_wevity_url(url) and not is_wevity_detail_url(url)


def load_prefill_data(source_url):
    # 이 함수는 상세 URL 하나를 받아서 저장 가능한 prefill dict로 변환하는
    # 공용 진입점이다. 수동 prefill 흐름이든 크롤러 내부 저장 흐름이든
    # 상세 페이지 데이터가 필요하면 반드시 이 함수를 거치도록 맞춘다.
    normalized_source_url = (source_url or "").strip()
    if not normalized_source_url:
        raise ValueError("Please enter a Wevity URL.")
    if not is_wevity_detail_url(normalized_source_url):
        raise ValueError("Please enter a Wevity detail URL for prefill.")

    try:
        return build_prefill_data(normalized_source_url)
    except Exception as exc:
        raise ValueError(f"Could not load prefill data: {exc}") from exc


def build_prefill_data(source_url):
    # 상세 페이지 HTML을 먼저 가져온 뒤, 저장에 필요한 필드만 파싱해서
    # contest_writer가 바로 사용할 수 있는 형태의 dict로 정리한다.
    html = fetch_detail_page(source_url)
    if not html or not html.strip():
        raise ValueError("Fetched page is empty.")

    detail_fields = parse_detail_fields(
        html=html,
        source_url=source_url,
        list_meta={},
    )

    # 상세 파서가 별도 detail_url을 찾지 못한 경우에는
    # 최소한 원본 상세 URL이라도 남기도록 fallback 한다.
    detail_url = detail_fields["detail_url"] or source_url

    return {
        "source_url": source_url,
        "detail_url": detail_url,
        "title": detail_fields["title"],
        "eligibility": detail_fields["eligibility"],
        "description": detail_fields["description"],
        "category": detail_fields["category"],
        "host_region": detail_fields["host_region"],
        "organizer": detail_fields["organizer"],
        "total_prize": detail_fields["total_prize"],
        "first_prize": detail_fields["first_prize"],
        "start_date": detail_fields["start_date"],
        "end_date": detail_fields["end_date"],
        "content_type": detail_fields["content_type"],
        "image_urls": detail_fields["image_urls"],
        "attachment_lines": detail_fields["attachment_lines"],
        # 현재 자동 수집으로 들어오는 공모전은 기본적으로 활성 상태로 본다.
        "is_active": True,
    }
