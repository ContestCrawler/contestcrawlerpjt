from contests.services.crawler import fetch_list_page
from contests.services.parser import parse_contest_list


def normalize_url(url):
    # strip():
    # - 좌우 공백 제거
    # rstrip("/"):
    # - 끝 슬래시 차이만 있는 URL을 동일하게 취급
    return (url or "").strip().rstrip("/")


def find_list_metadata(source_url):
    # fetch_list_page():
    # - Selenium으로 목록 HTML 수집
    # parse_contest_list():
    # - HTML에서 카드별 메타데이터(dict 리스트) 추출
    try:
        list_html = fetch_list_page()
        items = parse_contest_list(list_html)
    except Exception:
        # 목록 수집 실패 시 프리필 전체를 막지 않기 위해 빈 dict 반환
        return {}

    target = normalize_url(source_url)
    for item in items:
        # dict.get():
        # - 키 누락 시 KeyError 방지
        if normalize_url(item.get("detail_url", "")) == target:
            return {
                "title": item.get("title", ""),
                "region": item.get("region", ""),
                "start_date": item.get("start_date"),
                "end_date": item.get("end_date"),
            }
    return {}
