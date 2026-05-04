from urllib.parse import urlparse

from contests.services.detail_crawler import fetch_detail_page
from contests.services.prefill_detail_parser import parse_detail_fields
from contests.services.prefill_list_meta import find_list_metadata


def get_hostname(url):
    # urlparse()는 URL을 scheme/hostname/path/query 등으로 안전하게 분리한다.
    # 사이트별 분기는 문자열 contains보다 hostname 기준으로 보는 편이 오탐이 적다.
    hostname = urlparse(url or "").hostname or ""
    return hostname.lower()


def is_wevity_url(url):
    # 위비티는 상세 페이지 하나 안에 제목/분야/주최/기간/홈페이지가 모두 있다.
    # 그래서 목록 페이지 조회 없이 상세 HTML만 파싱하는 전용 흐름을 탄다.
    return get_hostname(url).endswith("wevity.com")


def build_prefill_data(source_url):
    # create 화면에서 "Load Prefill" 버튼을 눌렀을 때 호출되는 메인 조립 함수.
    # 반환 dict의 key는 ContestCreateForm(initial=...)에 그대로 들어가므로
    # forms.py의 필드 이름과 반드시 맞아야 한다.

    if is_wevity_url(source_url):
        # 위비티는 사용자가 넘긴 상세 URL 자체에서 필요한 메타데이터를 찾는다.
        # 공공데이터포털 목록과 구조가 다르므로 list_meta는 비워 둔다.
        list_meta = {}
    else:
        # 위비티가 아닌 URL은 현재 정책상 공공데이터포털 상세 URL로 간주한다.
        # 공공데이터포털은 제목/지역/기간이 목록 카드에 더 안정적으로 노출되므로
        # 먼저 목록 페이지에서 같은 detail_url을 찾아 메타데이터를 가져온다.
        list_meta = find_list_metadata(source_url)

    # 상세 페이지 HTML은 두 사이트 모두 필요하다.
    # 본문/이미지/첨부파일 및 목록에 없는 필드(분야, 주최사 등)를 여기서 보강한다.
    html = fetch_detail_page(source_url)
    if not html or not html.strip():
        raise ValueError("Fetched page is empty.")

    # 상세 HTML 파싱 결과와 list_meta를 합쳐 form 초기값 후보를 만든다.
    # parse_detail_fields 내부에서 list_meta 값이 있으면 제목/지역/날짜에 우선 적용한다.
    detail_fields = parse_detail_fields(
        html=html,
        source_url=source_url,
        list_meta=list_meta,
    )

    # DB의 detail_url은 "사용자가 입력한 크롤링 URL"이 아니라
    # 실제 공모전 페이지로 이동할 때 사용할 URL이다.
    # 공공데이터포털은 입력 URL을 그대로 쓰고, 위비티는 요약 영역의 "홈페이지" 값을 사용한다.
    detail_url = source_url
    if is_wevity_url(source_url):
        detail_url = detail_fields["detail_url"] or source_url

    # image_urls/attachment_lines는 실제 DB 모델 필드는 아니고,
    # 저장 시 contest_writer.save_assets()가 별도 테이블로 옮겨 담기 위한 보조 입력값이다.
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
        "is_active": True,
    }
