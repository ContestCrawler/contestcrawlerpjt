from django.shortcuts import render, redirect
from contests.models import Contest
from .service import MainServiceV1, CreateServiceV1


def index(request):
    service = MainServiceV1()
    context = service.get_context(request)
    return render(request, 'service/index.html', context)


def create(request):
    create_service = CreateServiceV1()
    context = create_service.get_context(request)
    if context == None:
        return redirect('services:index')
    return render(request, 'service/create.html', context)
