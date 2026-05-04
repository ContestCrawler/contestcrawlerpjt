from django.shortcuts import render, redirect
from services.schedule import Scheduller


def scheduled_update(request):
    scheduller = Scheduller()
    duplicated_pk = scheduller.start_crawl()
    # duplicated_pk 값은 크롤링 진행 이전 마지막 pk 값으로 가정
    scheduller.date_update_to(duplicated_pk)
    return