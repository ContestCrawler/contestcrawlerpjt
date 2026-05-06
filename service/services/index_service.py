from abc import ABC, abstractmethod
from ..repositories.contest_repo import ContestRepository



class Service(ABC):

    def __init__(self):
        self.repository = ContestRepository()
        self.categories = self.repository.get_distincted("category")

    @abstractmethod
    def get_context(self, request):
        pass


class ServiceV1(Service):

    def __init__(self):
        super().__init__()
        pass


    def get_contests_list(self, request):

        conditions = {
            'institution': request.GET.get('institution'),
            'region_name': request.GET.get('region_name'),
            'date': request.GET.get('date'),
            'category': request.GET.get('category'),
            'title__icontains': request.GET.get('search_word'),
            # 'description__icontains': request.GET.get('search_word'),
        }

        conditions = {
            key: value
            for key, value in conditions.items()
            if value
        }

        if conditions:
            contests = self.repository.get_filtered(conditions)
        else:
            contests = self.repository.get_all()

        # contests = ["공모전1", "공모전2", "공모전3"]  # 테스트용

        context = {
            # 'institutions': self.institutions,
            # 'regions': self.regions,
            'categories': self.categories,
            'contests': contests,
        }
        return context


    def get_contest_detail(self, contest_pk):
        contest_repository = ContestRepository()
        contest = contest_repository.get(contest_pk)
        contest_images = contest_repository.get_image(contest_pk)
        contest_attachments = contest_repository.get_attachment(contest_pk)
        context = {
            'contest': contest,
            'contest_images': contest_images,
            'contest_attachments': contest_attachments,
        }
        return context

