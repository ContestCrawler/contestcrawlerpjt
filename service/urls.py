from django.urls import path
from . import views

app_name = 'service'
urlpatterns = [
    path('', views.index, name='index'),
    path('filter/', views.filtering, name='filtering'),  # 추후 추가 url 없이 메인 url 하나로 관리 시도 예정
]
