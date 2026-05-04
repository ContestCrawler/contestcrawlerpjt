from django.shortcuts import render, redirect
from service.services.schedule import run_scheduled_update
from django.http import HttpResponse


def scheduled_update(request):
    run_scheduled_update()

    return HttpResponse(status=204)