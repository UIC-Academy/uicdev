from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
)

from apps.courses.models import Course
from apps.courses.serializers import CourseSerializer


class CourseListAPIView(ListAPIView):
    serializer_class = CourseSerializer

    def get_queryset(self):
        queryset = (
            Course.objects.filter(is_active=True)
            .select_related(
                "author",
                "category",
                "banner",
            )
            .prefetch_related(
                "tags",
            )
            .order_by("name")
        )
        return queryset


class CourseRetrieveAPIView(RetrieveAPIView):
    serializer_class = CourseSerializer

    def get_object(self):
        return (
            Course.objects.filter(is_active=True)
            .select_related(
                "author",
                "category",
                "tags",
                "banner",
                "modules__lessons",
            )
            .get(pk=self.kwargs["pk"])
        )
