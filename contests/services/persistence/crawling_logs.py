from django.utils import timezone

from service.models import CrawlingLog


STATUS_RUNNING = "running"


def create_running_crawling_log():
    """
    크롤링 실행 시작 상태의 CrawlingLog를 DB에 생성한다.

    역할:
        크롤링 흐름에서 사용할 로그 레코드를 먼저 만들고, 이후 Contest 저장 시 이 로그를 FK로 연결할 수 있게 한다.

    의미:
        CrawlingLog의 생성 책임을 persistence 계층에 두어 crawling 계층이 DB 생성 세부 구현을 직접 알지 않도록 분리한다.

    반환값:
        status가 running이고 count 값이 0으로 초기화된 CrawlingLog 모델 인스턴스를 반환한다.
    """
    return CrawlingLog.objects.create(
        status=STATUS_RUNNING,
        started_at=timezone.now(),
        total_count=0,
        created_count=0,
        updated_count=0,
        failed_count=0,
    )


def save_crawling_log_result(crawling_log, result, status):
    """
    크롤링 결과 count와 최종 status를 CrawlingLog에 저장한다.

    역할:
        크롤링 중 메모리에 누적한 실행 결과를 기존 CrawlingLog DB 레코드에 반영한다.

    의미:
        crawling 계층은 어떤 결과가 나왔는지만 전달하고, 실제 DB 업데이트 책임은 persistence 계층에서 처리한다.

    반환값:
        저장이 완료된 CrawlingLog 모델 인스턴스를 반환한다.

    에러 처리:
        이 함수 자체에서는 DB 저장 예외를 삼키지 않는다. 저장 실패는 호출한 크롤링 흐름 또는 스케줄러가 감지할 수 있도록
        상위로 전파한다.
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
