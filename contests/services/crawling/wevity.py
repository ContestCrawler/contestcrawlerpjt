from contests.services.crawling.fetchers import fetch_wevity_list_html
from contests.services.parsing.wevity_list import parse_wevity_list_page as parse_wevity_list_html
from contests.services.prefilling.url_rules import is_wevity_detail_url, is_wevity_list_url


DEFAULT_WEVITY_LIST_URL = "https://www.wevity.com/?c=find&s=1&gub=1&cidx=20"
STATUS_RUNNING = "running"
STATUS_SUCCESS = "success"
STATUS_PARTIAL_SUCCESS = "partial_success"
STATUS_FAILED = "failed"


def create_crawling_log():
    """
    Wevity 크롤링 실행 1회를 나타내는 CrawlingLog 객체를 생성한다.

    의미:
        스케줄러나 view가 별도 로그 객체를 만들지 않아도, 크롤링 로직 내부에서 이번 실행의 시작 상태를 DB에 남긴다.

    반환값:
        status가 running이고 count 값이 0으로 초기화된 CrawlingLog 모델 인스턴스를 반환한다.
    """
    from django.utils import timezone
    from service.models import CrawlingLog

    return CrawlingLog.objects.create(
        status=STATUS_RUNNING,
        started_at=timezone.now(),
        total_count=0,
        created_count=0,
        updated_count=0,
        failed_count=0,
    )


def new_crawling_result():
    """
    크롤링 결과 count를 누적할 기본 dict를 만든다.

    의미:
        CrawlingLog에 저장할 total/created/updated/failed 값을 크롤링 중 메모리에서 누적한다.

    반환값:
        total_count, created_count, updated_count, failed_count가 0인 dict를 반환한다.
    """
    return {
        "total_count": 0,
        "created_count": 0,
        "updated_count": 0,
        "failed_count": 0,
    }


def merge_crawling_result(total_result, page_result):
    """
    한 페이지 처리 결과를 전체 크롤링 결과에 누적한다.

    의미:
        페이지별로 계산된 count를 실행 전체 count로 합산해 CrawlingLog 최종 저장값을 만든다.

    반환값:
        total_result dict 자체를 갱신하고 그대로 반환한다.
    """
    for key in ("total_count", "created_count", "updated_count", "failed_count"):
        total_result[key] += page_result.get(key, 0)
    return total_result


def save_crawling_log_result(crawling_log, result, status):
    """
    크롤링 결과 count와 최종 status를 CrawlingLog에 저장한다.

    의미:
        크롤링 내부에서 누적한 실행 결과를 DB 로그 레코드에 반영한다.

    반환값:
        저장이 끝난 CrawlingLog 인스턴스를 반환한다.
    """
    crawling_log.status = status
    crawling_log.total_count = result["total_count"]
    crawling_log.created_count = result["created_count"]
    crawling_log.updated_count = result["updated_count"]
    crawling_log.failed_count = result["failed_count"]
    crawling_log.save(
        update_fields=[
            "status",
            "total_count",
            "created_count",
            "updated_count",
            "failed_count",
        ]
    )
    return crawling_log


def get_crawling_status(result):
    """
    누적된 크롤링 결과 count로 최종 로그 status를 결정한다.

    의미:
        일부 상세 저장만 실패한 경우 전체 실패가 아니라 부분 성공으로 기록하기 위한 분기다.

    반환값:
        실패 count가 0이면 success, 성공과 실패가 섞여 있으면 partial_success,
        처리한 모든 항목이 실패했으면 failed 문자열을 반환한다.
    """
    if result["failed_count"] == 0:
        return STATUS_SUCCESS
    if result["created_count"] > 0 or result["updated_count"] > 0:
        return STATUS_PARTIAL_SUCCESS
    return STATUS_FAILED


def crawl_wevity_contests(source_urls):
    """
    여러 Wevity 상세 URL을 순서대로 저장한다.

    의미:
        이미 수집 대상 상세 URL 목록을 알고 있을 때 사용하는 batch 진입점이다.

    반환값:
        CrawlingLog 인스턴스를 반환한다. 각 URL은 Contest 및 자산 레코드로 저장되고,
        저장된 Contest는 반환된 CrawlingLog를 FK로 참조한다.
    """
    crawling_log = create_crawling_log()
    result = new_crawling_result()

    for source_url in source_urls:
        result["total_count"] += 1
        try:
            save_wevity_contest_from_detail_url(source_url, crawling_log=crawling_log)
            result["created_count"] += 1
        except Exception:
            # Error handling:
            # 상세 URL 목록 batch에서도 1건 실패는 failed_count에 기록하고 다음 URL 처리를 계속한다.
            result["failed_count"] += 1
            continue

    return save_crawling_log_result(crawling_log, result, get_crawling_status(result))


def crawl_wevity_list(list_url):
    """
    Wevity 목록 URL에서 시작해 최신 공모전을 페이지 단위로 수집한다.

    의미:
        목록 페이지를 순회하면서 마감 공모전을 처음 만나면 최신 구간이 끝났다고 보고
        수집을 중단한다. 이미 방문한 페이지는 재방문하지 않는다.

    반환값:
        CrawlingLog 인스턴스를 반환한다. 수집한 상세 페이지는 DB에 저장되고,
        저장된 Contest는 반환된 CrawlingLog를 FK로 참조한다.

    예외:
        목록 URL이 비어 있거나 Wevity 목록 URL이 아니면 ValueError가 발생한다.
        상세 저장 과정의 예외는 상위 호출자에게 전달된다.
    """
    crawling_log = create_crawling_log()
    result = new_crawling_result()

    try:
        next_page_url = validate_wevity_list_url(list_url)
        visited_pages = set()

        while should_visit_page(next_page_url, visited_pages):
            visited_pages.add(next_page_url)
            page_result = crawl_wevity_list_once(next_page_url, crawling_log=crawling_log)
            merge_crawling_result(result, page_result)

            if page_result["should_stop"]:
                break

            next_page_url = page_result["next_page_url"]

        return save_crawling_log_result(crawling_log, result, get_crawling_status(result))
    except Exception:
        # Error handling:
        # 목록 fetch/파싱처럼 실행 자체를 계속할 수 없는 예외는 failed 로그로 저장한 뒤 상위 호출자가 감지하도록 다시 올린다.
        save_crawling_log_result(crawling_log, result, STATUS_FAILED)
        raise


def crawl_wevity_list_once(list_url, crawling_log=None):
    """
    Wevity 목록 한 페이지를 처리한다.

    의미:
        현재 페이지의 공모전 카드들을 순서대로 확인하고, 열린 공모전은 상세 저장까지 수행한다.
        마감 항목을 만나거나 목록 파싱 결과가 비어 있으면 전체 크롤링을 멈추도록 신호를 만든다.

    반환값:
        dict를 반환한다.
        - next_page_url: 다음 목록 페이지 URL. 중단해야 하면 빈 문자열.
        - should_stop: 상위 반복 크롤링을 중단해야 하면 True.
        - total_count: 저장 시도한 상세 URL 수.
        - created_count: 새로 저장된 Contest 수.
        - updated_count: 현재는 업데이트 저장 정책이 없으므로 0.
        - failed_count: 상세 저장에 실패한 Contest 수.
    """
    parsed_page = parse_wevity_list_url(list_url)
    items = parsed_page["items"]
    result = new_crawling_result()

    # Error handling:
    # 목록 구조가 바뀌었거나 파싱에 실패해 항목이 없으면 다음 페이지로 무리하게 진행하지 않는다.
    if not items:
        return {
            **result,
            "next_page_url": "",
            "should_stop": True,
        }

    for item in items:
        if item["is_closed"]:
            return {
                **result,
                "next_page_url": "",
                "should_stop": True,
            }

        result["total_count"] += 1
        try:
            save_wevity_contest_from_detail_url(item["detail_url"], crawling_log=crawling_log)
            result["created_count"] += 1
        except Exception:
            # Error handling:
            # 상세 1건 저장 실패는 failed_count에 기록하고 다음 공모전 처리를 계속한다.
            result["failed_count"] += 1
            continue

    return {
        **result,
        "next_page_url": parsed_page["next_page_url"],
        "should_stop": False,
    }


def parse_wevity_list_url(list_url):
    """
    Wevity 목록 URL을 HTML로 가져온 뒤 목록 파서 결과로 변환한다.

    의미:
        crawling 계층과 parsing 계층을 연결하는 작은 어댑터 역할을 한다.

    반환값:
        parse_wevity_list_html()의 결과 dict를 반환한다.
        - items: 상세 URL, 상태 텍스트, 마감 여부를 담은 목록
        - next_page_url: 다음 페이지 URL
    """
    list_html = fetch_wevity_list_html(list_url)
    return parse_wevity_list_html(list_html, list_url)


def save_wevity_contest_from_detail_url(source_url, crawling_log=None):
    """
    Wevity 상세 URL 하나를 prefill 데이터로 변환하고 Contest로 저장한다.

    의미:
        목록 크롤러가 발견한 상세 URL을 실제 DB 저장까지 연결하는 저장 진입점이다.

    반환값:
        생성된 Contest 인스턴스를 반환한다.
        crawling_log가 있으면 Contest.crawling_log FK에 함께 저장된다.

    예외:
        Wevity 상세 URL이 아니면 ValueError를 발생시킨다.
        상세 HTML fetch, 파싱, DB 저장 실패는 상위 호출자에게 전달된다.
    """
    from contests.services.persistence.contest_assets import create_contest_with_assets
    from contests.services.prefilling.builder import load_contest_prefill

    # Error handling:
    # 목록 URL이나 다른 사이트 URL이 저장 경로로 들어오는 실수를 초기에 차단한다.
    if not is_wevity_detail_url(source_url):
        raise ValueError(f"Only Wevity detail URLs are supported: {source_url}")

    prefill_data = load_contest_prefill(source_url)
    return create_contest_with_assets(prefill_data, crawling_log=crawling_log)


def validate_wevity_list_url(list_url, is_list_url_checker=None):
    """
    입력값이 Wevity 목록 URL인지 검증하고 앞뒤 공백을 제거한 URL을 반환한다.

    의미:
        view나 command에서 받은 사용자 입력을 크롤러가 처리 가능한 형태로 보정한다.

    반환값:
        공백이 제거된 Wevity 목록 URL 문자열을 반환한다.

    예외:
        URL이 비어 있거나 검사 함수가 False를 반환하면 ValueError를 발생시킨다.
    """
    is_list_url_checker = is_list_url_checker or is_wevity_list_url
    normalized_list_url = (list_url or "").strip()

    # Error handling:
    # 비어 있는 입력과 상세 URL 입력을 같은 사용자 메시지로 막아 크롤러 오작동을 피한다.
    if not normalized_list_url:
        raise ValueError("Please enter a Wevity list URL.")
    if not is_list_url_checker(normalized_list_url):
        raise ValueError("Please enter a Wevity list URL.")

    return normalized_list_url


def should_visit_page(next_page_url, visited_pages):
    """
    다음 페이지 URL을 방문해도 되는지 판단한다.

    의미:
        빈 URL과 이미 방문한 URL을 제외해 무한 루프를 막는다.

    반환값:
        방문할 URL이 있고 아직 방문하지 않았으면 True, 아니면 False를 반환한다.
    """
    return bool(next_page_url) and next_page_url not in visited_pages


def crawl_latest_wevity_contests(list_url=DEFAULT_WEVITY_LIST_URL):
    """
    기본 Wevity 목록 URL을 기준으로 최신 공모전 수집을 시작한다.

    의미:
        스케줄러나 관리 명령에서 인자 없이 호출하기 좋은 기본 크롤링 진입점이다.

    반환값:
        crawl_wevity_list()가 저장한 CrawlingLog 인스턴스를 반환한다.
    """
    return crawl_wevity_list(list_url)
