from django.shortcuts import render, redirect
from contests.models import Contest


# Create your views here.
def index(request):
    contests = Contest.objects.all()
    context = {
        'contests': contests,
    }
    return render(request, 'service/index.html', context)


# 필터링 함수
def filtering(request):
    context = {
    
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