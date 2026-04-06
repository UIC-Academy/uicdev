from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    GenericAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response

from apps.common.models import Country, Region
from apps.common.serializers.country_region import CountrySerializer, RegionSerializer
from apps.common.tasks import import_countries_and_regions


class ImportDataAPIView(GenericAPIView):
    def post(self, request, *args, **kwargs):
        result = import_countries_and_regions.delay()
        return Response(
            {
                "message": "Import task started",
                "task_id": result.id,
            }
        )


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
