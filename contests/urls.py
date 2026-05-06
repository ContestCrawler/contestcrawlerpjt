from django.urls import path

from . import views

app_name = "contests"

urlpatterns = [
    path("create/", views.create_contest, name="create"),
    path("create/prefill/", views.prefill_contest, name="prefill"),
]
