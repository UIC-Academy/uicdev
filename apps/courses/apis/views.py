from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny

from apps.courses.apis.serializers import (
    CategorySerializer,
    CourseSerializer,
    TagSerializer,
)
from apps.courses.models import Category, Course, Tag


class CategoryListCreateAPIView(ListCreateAPIView):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class CategoryRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer


class TagListCreateAPIView(ListCreateAPIView):
    queryset = Tag.objects.all().order_by("name")
    serializer_class = TagSerializer


class TagRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class CourseListCreateAPIView(ListCreateAPIView):
    queryset = Course.objects.select_related("author", "banner", "category").all()
    serializer_class = CourseSerializer
