from django.urls import path

from .views.index import index
from .views.detail import detail
from .views.scheduled_update import scheduled_update


app_name = 'service'


urlpatterns = [
    path('', index, name='index'),
    path('startcontestcrawler/', scheduled_update, name='scheduled_update'),
    path('<int:contest_pk>/', detail, name='detail'),
]
