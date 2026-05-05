from django.db import models


class CrawlingLog(models.Model):
    """
    status: 실행 결과 ( 성공, 실패 등)  
    started_at: 시작 시간  
    finished_at: 종료 시간 ( save 시간으로 저장 )  

    total_count: 처리한 데이터 수  
    created: 신규 데이터  
    updated: 갱신 데이터  
    ~~skipped: 중복 데이터 ( 프로젝트 특성 상 의미 없다고 판단, 추후 필요 시 주석 해제)~~  
    failed: 실패 수  

    ~~error_message: 현재 코드가 예외를 따로 구분하지 않고 있기 때문에 불필요~~  
    ~~traceback: 이게 뭘까?~~
    """

    status = models.CharField(max_length=50)
    started_at = models.DateTimeField()    
    finished_at = models.DateTimeField(auto_now_add=True)    

    total_count = models.IntegerField(default=None)
    created_count = models.IntegerField(default=None)
    updated_count = models.IntegerField(default=None)
    # skipped_count = models.IntegerField()
    failed_count = models.IntegerField(default=None)

    # error_message = models.TextField()
    # traceback = models.TextField()