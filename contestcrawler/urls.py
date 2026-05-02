"""
URL configuration for contestcrawler project.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("contests/", include("contests.urls")),
]
