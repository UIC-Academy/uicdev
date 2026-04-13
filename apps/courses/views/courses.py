from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)

from apps.courses.models import Course
from apps.courses.serializers import CourseSerializer


class CourseCreateAPIView(CreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class CourseListAPIView(ListAPIView):
    queryset = Course.objects.all().order_by("name")
    serializer_class = CourseSerializer


class CourseRetrieveAPIView(RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class CourseUpdateAPIView(UpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class CourseDeleteAPIView(DestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
