from abc import ABC, abstractmethod
from .repositories import ContestRepository



class Service(ABC):
    institutions = [
        '정부',
        '사설',
    ]
    regions = [
        '서울',
        '경기',
    ]
    categories = [
        '빅데이터',
        'IT',
    ]

    def __init__(self):
        self.repository = ContestRepository()


    @abstractmethod
    def get_context(self, request):
        pass


class MainServiceV1(Service):

    def __init__(self):
        super().__init__()
        pass


    def get_context(self, request):

        conditions = {
            'institution': request.GET.get('institution'),
            'region_name': request.GET.get('region_name'),
            'date': request.GET.get('date'),
            'category': request.GET.get('category'),
            'title__lookup': request.GET.get('search_word'),
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

        contests = ["공모전1", "공모전2", "공모전3"]  # 테스트용

        context = {
            'institutions': self.institutions,
            'regions': self.regions,
            'categories': self.categories,
            'contests': contests,
            # 'title__lookup': title__lookup,
        }
        return context


class CreateServiceV1():
    def __init__(self):
        pass

    
    def get_context(self, request):
        if request.method == "POST":
            contest_form = 'modelForm(request.POST)'
            if contest_form.is_valid():
                contest_form.save()
        else:
            contest_form = 'modelForm()'
            context = {
                'contest_form': contest_form,
            }        
            return context
