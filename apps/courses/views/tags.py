from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)

from apps.courses.models import Tag
from apps.courses.serializers import TagSerializer


class TagCreateAPIView(CreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class TagListAPIView(ListAPIView):
    queryset = Tag.objects.all().order_by("name")
    serializer_class = TagSerializer


class TagRetrieveAPIView(RetrieveAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class TagUpdateAPIView(UpdateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class TagDeleteAPIView(DestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
