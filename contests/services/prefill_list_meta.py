from contests.services.crawler import fetch_list_page
from contests.services.parser import parse_contest_list


def normalize_url(url):
    # 공공데이터포털 목록 카드의 detail_url과 사용자가 입력한 URL을 비교하기 위한 정규화.
    # 끝의 "/" 하나 때문에 같은 URL이 다르게 취급되는 문제를 막는다.
    return (url or "").strip().rstrip("/")


def find_list_metadata(source_url):
    # 공공데이터포털 전용 목록 메타 조회 함수.
    #
    # 이 프로젝트의 기존 방식은 다음 순서였다.
    # 1. 공공데이터포털 목록 페이지를 Selenium으로 가져온다.
    # 2. 목록 카드들을 parse_contest_list()로 파싱한다.
    # 3. 사용자가 입력한 상세 URL과 같은 카드의 title/region/date를 가져온다.
    #
    # 위비티에는 이 목록 매칭 단계가 맞지 않기 때문에 prefill.py에서 위비티 URL은
    # 이 함수를 호출하지 않는다.
    try:
        list_html = fetch_list_page()
        items = parse_contest_list(list_html)
    except Exception:
        # 목록 페이지 수집 실패가 prefill 전체 실패로 이어지면 사용자가 아무 값도 못 받는다.
        # 그래서 빈 dict를 반환하고, 상세 HTML 파서가 가능한 값만 보강하도록 둔다.
        return {}

    target = normalize_url(source_url)
    for item in items:
        if normalize_url(item.get("detail_url", "")) == target:
            # host_region은 새 모델 필드명이다.
            # 기존 parser 결과나 과거 코드가 region이라는 key를 줄 수도 있어 fallback을 둔다.
            return {
                "title": item.get("title", ""),
                "host_region": item.get("host_region", "") or item.get("region", ""),
                "start_date": item.get("start_date"),
                "end_date": item.get("end_date"),
            }
    return {}
