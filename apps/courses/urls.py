from django.urls import path

from apps.courses.apis import (
    CategoryListCreateAPIView,
    CategoryRetrieveUpdateDestroyAPIView,
    CourseListCreateAPIView,
    TagListCreateAPIView,
    TagRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("categories/", CategoryListCreateAPIView.as_view(), name="category-list"),
    path(
        "categories/<int:pk>/",
        CategoryRetrieveUpdateDestroyAPIView.as_view(),
        name="category-detail",
    ),
    path("tags/", TagListCreateAPIView.as_view(), name="tag-list"),
    path(
        "tags/<int:pk>/",
        TagRetrieveUpdateDestroyAPIView.as_view(),
        name="tag-detail",
    ),
    path("", CourseListCreateAPIView.as_view(), name="course-list"),
    # path(
    #     "courses/<int:pk>/",
    #     CourseRetrieveUpdateDestroyAPIView.as_view(),
    #     name="course-detail",
    # )
]
