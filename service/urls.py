from django.urls import path
from . import views

app_name = 'serice'
urlpatterns = [
    path('', views.index, name='index'),
]
