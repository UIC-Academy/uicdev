from .category import (
    CategoryCreateAPIView,
    CategoryDeleteAPIView,
    CategoryListAPIView,
    CategoryRetrieveAPIView,
    CategoryUpdateAPIView,
)
from .courses import (
    CourseListAPIView,
    CourseRetrieveAPIView,
)
from .tags import TagCreateAPIView, TagDeleteAPIView, TagListAPIView, TagRetrieveAPIView, TagUpdateAPIView

__all__ = [
    "CategoryListAPIView",
    "CategoryCreateAPIView",
    "CategoryUpdateAPIView",
    "CategoryRetrieveAPIView",
    "CategoryDeleteAPIView",
    "TagListAPIView",
    "TagCreateAPIView",
    "TagUpdateAPIView",
    "TagRetrieveAPIView",
    "TagDeleteAPIView",
    "CourseListAPIView",
    "CourseRetrieveAPIView",
]
