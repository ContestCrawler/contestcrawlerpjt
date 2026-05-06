from contests.services.crawling.fetchers import fetch_wevity_list_html
from contests.services.parsing.wevity_list import parse_wevity_list_items


def normalize_url(url):
    """
    URL 비교용 정규화 문자열을 만든다.

    의미:
        끝의 slash 차이 때문에 같은 URL이 다르게 비교되는 문제를 줄인다.

    반환값:
        앞뒤 공백과 마지막 slash가 제거된 문자열을 반환한다.
    """
    return (url or "").strip().rstrip("/")


def find_list_metadata(source_url, list_url=None):
    """
    목록 페이지에서 특정 상세 URL에 해당하는 보조 메타데이터를 찾는다.

    의미:
        상세 페이지에서 부족할 수 있는 제목, 지역, 날짜 정보를 목록 카드에서 보강하기 위한 함수다.

    반환값:
        매칭되는 목록 항목이 있으면 title, host_region, start_date, end_date dict를 반환한다.
        목록 URL이 없거나 조회/파싱/매칭에 실패하면 빈 dict를 반환한다.
    """
    # Error handling:
    # list_url이 없으면 목록 보강을 시도할 수 없으므로 빈 메타데이터로 안전하게 종료한다.
    if not list_url:
        return {}

    try:
        list_html = fetch_wevity_list_html(list_url)
        items = parse_wevity_list_items(list_html, list_url)
    except Exception:
        # Error handling:
        # 목록 메타데이터는 보조 정보이므로 실패해도 prefill 전체를 실패시키지 않는다.
        return {}

    target = normalize_url(source_url)
    for item in items:
        if normalize_url(item.get("detail_url", "")) == target:
            return {
                "title": item.get("title", ""),
                "host_region": item.get("host_region", "") or item.get("region", ""),
                "start_date": item.get("start_date"),
                "end_date": item.get("end_date"),
            }
    return {}
