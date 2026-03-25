from django.urls import path

from apps.common.apis import (
    CountryListCreateAPIView,
    CountryRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("countries/", CountryListCreateAPIView.as_view(), name="country-list"),
    path(
        "countries/<int:pk>/",
        CountryRetrieveUpdateDestroyAPIView.as_view(),
        name="country-detail",
    ),
]
