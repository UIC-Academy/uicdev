from django.urls import path

from apps.accounts.views import home

urlpatterns = [
    path("", home, name="home"),
]
