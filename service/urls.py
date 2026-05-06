from django.urls import path

from . import views

app_name = 'service'


urlpatterns = [
    path('', views.index, name='index'),
    path('<int:contest_pk>/', views.detail, name='detail'),
]
