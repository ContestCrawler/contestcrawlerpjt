from service.models import CrawlingLog


class CrawlingLogRepository():
    def __init__(self):
        pass


    def save(self, CrawlingLog: CrawlingLog) -> None:
        """
        DB에 로그 저장
        """
        CrawlingLog.save()
        pass


    def get_all(self) -> None:
        """
        모든 로그 QuerySet 반환
        """
        return CrawlingLog.objects.all()