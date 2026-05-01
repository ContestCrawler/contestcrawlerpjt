from django.db import models

class Contest(models.Model):
    title = models.CharField(max_length=255)
    eligibility = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    detail_url = models.URLField(unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(auto_now=True)

