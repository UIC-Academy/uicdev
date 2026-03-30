from django.urls import path

from apps.common.views import (
    CountryListCreateAPIView,
    CountryRetrieveUpdateDestroyAPIView,
    FileUploadAPIView,
    RegionCreateAPIView,
    RegionDeleteAPIView,
    RegionListAPIView,
    RegionRetriveAPIView,
    RegionUpdateAPIView,
)

urlpatterns = [
    path("countries/", CountryListCreateAPIView.as_view(), name="country-list"),
    path(
        "countries/<int:pk>/",
        CountryRetrieveUpdateDestroyAPIView.as_view(),
        name="country-detail",
    ),
    path("regions/list/", RegionListAPIView.as_view(), name="region-list"),
    path("region/create/", RegionCreateAPIView.as_view(), name="region-create"),
    path("region/delete/<int:pk>", RegionDeleteAPIView.as_view(), name="region-delete"),
    path("region/update/<int:pk>", RegionUpdateAPIView.as_view(), name="region-update"),
    path("region/<int:pk>", RegionRetriveAPIView.as_view(), name="region-single"),
    path("file-upload/", FileUploadAPIView.as_view(), name="file-upload"),
]
