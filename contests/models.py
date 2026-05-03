from django.db import models

class Contest(models.Model):
    CONTENT_TYPE_CHOICES = [
        ("text", "텍스트"),
        ("image", "이미지"),
        ("file", "첨부파일"),
        ("mixed", "혼합"),
        ("unknown", "알 수 없음")
    ]
    
    title = models.CharField(max_length=255)
    
    eligibility = models.TextField(blank=True)
    description = models.TextField(blank=True)
    
    category = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    detail_url = models.URLField(unique=True)
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default="unknown"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)


class ContestImage(models.Model):
    
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name="images"
    )
    
    image_url = models.URLField()
    alt_text = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    
class ContestAttachment(models.Model):
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
