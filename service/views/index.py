from django.shortcuts import render, redirect
from contests.models import Contest
from ..services.index_service import ServiceV1


def index(request):
    service = ServiceV1()
    context = service.get_context(request)

    return render(request, 'service/index.html', context)
