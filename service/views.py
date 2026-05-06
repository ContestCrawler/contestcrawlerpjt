from django.shortcuts import render, redirect
from service.services.index_service import ServiceV1


# Service 메서드를 제공할 객체
service = ServiceV1()

# 메인페이지 표시할 공모전 리스트업 함수
def index(request):
    context = service.get_contests_list(request)
    return render(request, 'service/index.html', context)

# 공모전 상세 페이지 렌더링 함수
def detail(request, contest_pk):
    context = service.get_contest_detail(contest_pk)
    return render(request, 'service/detail.html', context)
