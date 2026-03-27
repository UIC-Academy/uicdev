from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
)

from apps.common.apis.serializers import CountrySerializer, RegionSerializer
from apps.common.models import Country, Region


class CountryListCreateAPIView(ListCreateAPIView):
    queryset = Country.objects.all().order_by("name")
    serializer_class = CountrySerializer


class CountryRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class RegionListAPIView(ListAPIView):
    queryset = Region.objects.all().order_by("name")
    serializer_class = RegionSerializer


class RegionRetriveAPIView(RetrieveAPIView):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class RegionCreateAPIView(CreateAPIView):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class RegionUpdateAPIView(UpdateAPIView):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class RegionDeleteAPIView(DestroyAPIView):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
