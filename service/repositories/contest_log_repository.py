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


    def get_all(self):
        """
        모든 로그 QuerySet 반환
        """
        return CrawlingLog._objects.all()
    

    def filter_success(self):
        """
        성공한 로그 QuerySet 반환
        """
        return CrawlingLog._objects.filter(status='success')
    

    def filter_fail(self):
        """
        실패한 로그 QuerySet 반환
        """
        return CrawlingLog._objects.filter(status='fail')