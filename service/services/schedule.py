# from contests.trigger import trigger
from django.db.models.functions import Now
from service.repositories.contest_repo import ContestRepository
from contests.services.crawling.wevity import crawl_latest_wevity_contests


contest_repository = ContestRepository()


# 크롤링 시작 트리거 함수
def start_crawl():
    crawl_latest_wevity_contests()


# 실행 당시 날짜를 기준으로 종료 날짜기 지난 공모전 필터링 후
# 필터링된 공모전 비활성화 및 soft delete
def date_update_to():
    activated_date = Now()

    conditions = {
        'end_date__lt': activated_date,
    }
    contests = contest_repository.get_filtered(conditions)

    for contest in contests:
        contest.is_active = False
        contest.deleted_at = activated_date
        contest.save()


def run_scheduled_update():
    start_crawl()
    date_update_to()
