from django.core.management.base import BaseCommand
from service.services.schedule import run_scheduled_update


class Command(BaseCommand):
    help = '공모전 데이터를 크롤링하고 날짜 정보를 업데이트합니다.'

    def handle(self, *args, **options):
        self.stdout.write('크롤링 시작')
        run_scheduled_update()
        self.stdout.write(self.style.SUCCESS('크롤링 완료'))