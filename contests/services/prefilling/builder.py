from contests.services.crawling.fetchers import fetch_detail_html
from contests.services.parsing.detail_router import parse_detail_fields


def load_contest_prefill(source_url):
    """
    상세 URL을 Contest 생성용 prefill dict로 변환한다.

    의미:
        사용자 입력 또는 크롤러가 넘긴 URL을 검증 가능한 단일 진입점으로 받아,
        fetch/parsing 과정의 예외를 사용자에게 보여줄 수 있는 ValueError로 감싼다.

    반환값:
        build_contest_prefill()이 만든 prefill dict를 반환한다.

    예외:
        URL이 비어 있으면 ValueError를 발생시킨다.
        fetch/parsing 중 발생한 예외는 메시지를 붙여 ValueError로 다시 발생시킨다.
    """
    normalized_source_url = (source_url or "").strip()
    # Error handling:
    # 빈 입력은 네트워크 요청까지 보내지 않고 즉시 사용자 입력 오류로 처리한다.
    if not normalized_source_url:
        raise ValueError("Please enter a Wevity URL.")

    try:
        return build_contest_prefill(normalized_source_url)
    except Exception as exc:
        # Error handling:
        # 하위 계층의 다양한 예외를 prefill 실패라는 하나의 의미로 정리해 view에서 다루기 쉽게 한다.
        raise ValueError(f"Could not load prefill data: {exc}") from exc


def build_contest_prefill(source_url):
    """
    상세 페이지 HTML을 읽어 Contest 저장에 필요한 prefill dict를 만든다.

    의미:
        fetch_detail_html()로 HTML을 가져오고, 사이트별 상세 파서 결과를
        Contest 모델과 자산 저장 함수가 바로 사용할 수 있는 key 구조로 정리한다.

    반환값:
        source_url, detail_url, title, eligibility, description, category,
        host_region, organizer, prize/date/content/asset 필드를 담은 dict를 반환한다.

    예외:
        가져온 HTML이 비어 있으면 ValueError를 발생시킨다.
        fetch 또는 parse 실패는 원래 예외 그대로 상위 호출자에게 전달된다.
    """
    html = fetch_detail_html(source_url)
    # Error handling:
    # 빈 HTML은 파서에 넘겨도 의미 있는 값을 만들 수 없으므로 명확한 실패로 처리한다.
    if not html or not html.strip():
        raise ValueError("Fetched page is empty.")

    detail_fields = parse_detail_fields(
        html=html,
        source_url=source_url,
        list_meta={},
    )

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
        "is_active": True,
    }
