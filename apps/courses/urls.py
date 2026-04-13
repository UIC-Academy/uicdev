from django.urls import path

from apps.courses.views import (
    CategoryCreateAPIView,
    CategoryDeleteAPIView,
    CategoryListAPIView,
    CategoryRetrieveAPIView,
    CategoryUpdateAPIView,
    CourseCreateAPIView,
    CourseDeleteAPIView,
    CourseListAPIView,
    CourseRetrieveAPIView,
    CourseUpdateAPIView,
    TagCreateAPIView,
    TagDeleteAPIView,
    TagListAPIView,
    TagRetrieveAPIView,
    TagUpdateAPIView,
)

urlpatterns = [
    path("tags/", TagListAPIView.as_view(), name="tag-list"),
    path("tags/create/", TagCreateAPIView.as_view(), name="tag-create"),
    path("tags/<int:pk>/", TagRetrieveAPIView.as_view(), name="tag-retrieve"),
    path("tags/<int:pk>/update/", TagUpdateAPIView.as_view(), name="tag-update"),
    path("tags/<int:pk>/delete/", TagDeleteAPIView.as_view(), name="tag-delete"),
    path("categories/", CategoryListAPIView.as_view(), name="category-list"),
    path("categories/create/", CategoryCreateAPIView.as_view(), name="category-create"),
    path("categories/<int:pk>/", CategoryRetrieveAPIView.as_view(), name="category-retrieve"),
    path("categories/<int:pk>/update/", CategoryUpdateAPIView.as_view(), name="category-update"),
    path("categories/<int:pk>/delete/", CategoryDeleteAPIView.as_view(), name="category-delete"),
    path("courses/", CourseListAPIView.as_view(), name="course-list"),
    path("courses/create/", CourseCreateAPIView.as_view(), name="course-create"),
    path("courses/<int:pk>/", CourseRetrieveAPIView.as_view(), name="course-retrieve"),
    path("courses/<int:pk>/update/", CourseUpdateAPIView.as_view(), name="course-update"),
    path("courses/<int:pk>/delete/", CourseDeleteAPIView.as_view(), name="course-delete"),
]
