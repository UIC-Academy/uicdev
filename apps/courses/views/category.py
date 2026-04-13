from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)

from apps.courses.models import Category
from apps.courses.serializers import CategorySerializer


class CategoryCreateAPIView(CreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryListAPIView(ListAPIView):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer


class CategoryRetrieveAPIView(RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryUpdateAPIView(UpdateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryDeleteAPIView(DestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
