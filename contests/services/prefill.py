from contests.services.detail_crawler import fetch_detail_page
from contests.services.prefill_detail_parser import parse_detail_fields
from contests.services.prefill_list_meta import find_list_metadata


def build_prefill_data(source_url):
    # 서비스 흐름:
    # 1) 리스트 메타 조회
    # 2) 상세 HTML 수집
    # 3) 상세 파싱
    # 4) form initial 구조로 병합

    # find_list_metadata():
    # - 리스트 페이지에서 title/region/date를 가져온다.
    # - 상세 파싱보다 안정적인 값(특히 날짜)을 우선 사용하기 위함.
    list_meta = find_list_metadata(source_url)

    # fetch_detail_page():
    # - 상세 URL의 HTML 원문 수집.
    # - 내부에서 requests 우선, 필요 시 Selenium fallback 사용.
    html = fetch_detail_page(source_url)
    if not html or not html.strip():
        # strip():
        # - 공백만 있는 문자열도 "빈 응답"으로 간주.
        raise ValueError("Fetched page is empty.")

    # parse_detail_fields():
    # - 텍스트/이미지/첨부/라벨 필드를 상세 HTML에서 추출.
    detail_fields = parse_detail_fields(
        html=html,
        source_url=source_url,
        list_meta=list_meta,
    )

    # 반환 딕셔너리는 ContestCreateForm(initial=...)에서 키 이름이 맞아야 한다.
    return {
        "source_url": source_url,
        "detail_url": source_url,
        "title": detail_fields["title"],
        "eligibility": detail_fields["eligibility"],
        "description": detail_fields["description"],
        "category": detail_fields["category"],
        "region": detail_fields["region"],
        "start_date": list_meta.get("start_date"),
        "end_date": list_meta.get("end_date"),
        "content_type": detail_fields["content_type"],
        "image_urls": detail_fields["image_urls"],
        "attachment_lines": detail_fields["attachment_lines"],
        "is_active": True,
    }
