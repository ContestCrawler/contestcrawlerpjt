from django.shortcuts import render, redirect
from ..repositories.contest_repo import ContestRepository


def detail(request, contest_pk):
    contest_repository = ContestRepository()
    contest = contest_repository.get_detail(contest_pk)
    contest_images = contest_repository.get_image(contest_pk)
    contest_attachments = contest_repository.get_attachment(contest_pk)
    context = {
        'contest': contest,
        'contest_images': contest_images,
        'contest_attachments': contest_attachments,
    }
    return render(request, 'service/detail.html', context)
