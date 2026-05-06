from django.db import models


class Contest(models.Model):
    _objects = models.Manager()

    # 상세 페이지 본문이 어떤 매체 중심인지 분류한다.
    # 관리자가 저장 전에 빠르게 검토하거나, 서비스 화면에서 표시 방식을 나눌 때 사용할 수 있다.
    CONTENT_TYPE_CHOICES = [
        ("text", "텍스트"),
        ("image", "이미지"),
        ("file", "첨부파일"),
        ("mixed", "혼합"),
        ("unknown", "알 수 없음")
    ]
    
    # 공모전의 대표 제목.
    # 공공데이터포털은 목록 카드의 제목을 우선 사용하고, 위비티는 상세 요약 블록 위 제목을 사용한다.
    title = models.CharField(max_length=255)
    
    # eligibility: 응모대상/참가자격.
    # description: 상세 페이지 본문에서 추출한 설명 텍스트.
    eligibility = models.TextField(blank=True)
    description = models.TextField(blank=True)
    
    # category: 분야/분류.
    # host_region: 주최지역. 예전 region 필드가 하던 역할을 더 명확한 이름으로 바꾼 필드다.
    # organizer: 주최사/주관기관. 지역과 의미가 섞이지 않도록 별도 필드로 분리했다.
    # total_prize, first_prize: 위비티 요약 영역 등에 노출되는 상금 정보.
    category = models.CharField(max_length=100, blank=True)
    host_region = models.CharField(max_length=100, blank=True)
    organizer = models.CharField(max_length=255, blank=True)
    total_prize = models.CharField(max_length=100, blank=True)
    first_prize = models.CharField(max_length=100, blank=True)
    
    # 접수 시작일/마감일. 일부 상세 페이지에서 날짜를 못 찾을 수 있어 null/blank를 허용한다.
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # 실제 공모전 페이지로 이동할 URL.
    # 공공데이터포털 입력 시에는 입력 URL을, 위비티 입력 시에는 요약 영역의 홈페이지 URL을 저장한다.
    detail_url = models.URLField(unique=True)
    crawling_log = models.ForeignKey(
        "service.CrawlingLog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contests",
    )
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default="unknown"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)


class ContestImage(models.Model):
    # 상세 페이지에서 발견한 이미지들을 Contest와 1:N 관계로 저장한다.
    
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name="images"
    )
    
    image_url = models.URLField()
    alt_text = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    
class ContestAttachment(models.Model):
    # 상세 페이지에서 발견한 첨부파일들을 Contest와 1:N 관계로 저장한다.
    FILE_TYPE_CHOICES = [
        ("pdf", "PDF"),
        ("hwp", "HWP"),
        ("hwpx", "HWPX"),
        ("doc", "DOC"),
        ("docx", "DOCX"),
        ("zip", "ZIP"),
        ("etc", "ETC")
    ]
    
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name="attachments"
    )
    
    file_name = models.CharField(max_length=255)
    file_url = models.URLField()
    file_type = models.CharField(
        max_length=20,
        choices=FILE_TYPE_CHOICES,
        default="etc",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
