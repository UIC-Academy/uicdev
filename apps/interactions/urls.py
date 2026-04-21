from django.urls import path

from apps.interactions.views import LessonFavoriteAPIView, LessonProgressAPIView, LessonRateAPIView

urlpatterns = [
    path("lessons/<int:lesson_id>/progress/", LessonProgressAPIView.as_view(), name="lesson-progress"),
    path("lessons/<int:lesson_id>/favorite/", LessonFavoriteAPIView.as_view(), name="lesson-favorite"),
    path("lessons/<int:lesson_id>/rate/", LessonRateAPIView.as_view(), name="lesson-rate"),
]
