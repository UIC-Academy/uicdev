from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from apps.common.apis.serializers import CountrySerializer
from apps.common.models import Country


class CountryListCreateAPIView(ListCreateAPIView):
    queryset = Country.objects.all().order_by("name")
    serializer_class = CountrySerializer


class CountryRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
