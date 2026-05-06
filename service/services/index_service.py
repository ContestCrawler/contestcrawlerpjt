from ..repositories.contest_repo import ContestRepository


class Service():

    def __init__(self):
        self.contest_repository = ContestRepository()
        pass


    def get_contests_list(self, request):
        """
        request 에서 검색 조건들로 필터링 후 필터링 된 QuerySet 반환
        """
        # 추후 검색 조건 추가 시 conditions 에 추가
        conditions = {
            'title__icontains': request.GET.get('search_word'),
        }

        # 검색 조건이 많아지면 사용자로부터 입력받은 값만 사용하도록 함
        conditions = {
            key: value
            for key, value in conditions.items()
            if value
        }

        if conditions:
            contests = self.contest_repository.get_filtered(conditions)
        else:
            contests = self.contest_repository.get_all()

        context = {
            'contests': contests,
        }
        return context


    def get_contest_detail(self, contest_pk):
        """
        공모전 상세 페이지 정보를 꺼내오는 함수
        """
        contest = self.contest_repository.get(contest_pk)
        contest_images = self.contest_repository.get_image(contest_pk)
        contest_attachments = self.contest_repository.get_attachment(contest_pk)
        context = {
            'contest': contest,
            'contest_images': contest_images,
            'contest_attachments': contest_attachments,
        }
        return context

