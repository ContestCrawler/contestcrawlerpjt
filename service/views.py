from django.shortcuts import render, redirect
from contests.models import Contest
from .repositories import Repository as Repo


repository = Repo()
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

def index(request):

    """
    필터링 기능 ( 사용 시 docstring 제거 후 사용, 하단부 리스트는 테스트용 contests )
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

    contests = repository.get_data(conditions)
    """
    contests = ["공모전1", "공모전2", "공모전3"]  # 테스트용
    context = {
        'institutions': institutions,
        'regions': regions,
        'categories': categories,
        'contests': contests,
        # 'title__lookup': title__lookup,
    }
    return render(request, 'service/index.html', context)



"""

0. 1일 1회 데이터 수집 진행

== 복잡한 로직이 없어서 관통 프로젝트 같이 인덱스 페이지 하나로 가능할 듯 ==

1. 인덱스 페이지에서 전체 데이터 조회
2. 분류, 정렬 조건 선택
3. 데이터 분류 및 정렬 > 동적 페이지로 해야하나?
  - 추가 페이지 구성 필요 없음
  - 간단한 요약 및 클릭 연결

"""