# from contests.trigger import trigger
from django.utils import timezone
from repositories.contest_repo import ContestRepository


class Scheduller():
    contest_repository = ContestRepository()

    def __init__(self):
        pass


    def start_crawl(self):
        # return trigger()
        # trigger() 함수가 중복 데이터 pk 값 반환

        pass


    def date_update_to(self, limit_pk):
        # pk 가 limit_pk 보다 작고 아직 종료되지 않은 공모전을 filtering 하는 conditions
        conditions = {
            'pk__lt': limit_pk,
            'is_active': True,
        }
        contests = self.contest_repository.get_filtered(conditions)

        activated_date = timezone.localdate

        for contest in contests:
            if contest.end_date < activated_date:
                contest.is_active = False
                contest.deleted_at = activated_date
                contest.save()
            else:
                contest.updated_at = activated_date
        pass