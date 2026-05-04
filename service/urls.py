from django.urls import path
from .views.index import index
from .views.detail import detail

app_name = 'service'
urlpatterns = [
    path('', index, name='index'),
    path('<int:contest_pk>/', detail, name='detail'),
]
