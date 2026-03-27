from django.urls import path

from apps.accounts.apis import (
    AuthorCreateApiViews,
    AuthorDeleteApiViews,
    AuthorDetailApiViews,
    AuthorListApiViews,
    AuthorUpdateApiViews,
    EducationCreateApiViews,
    EducationDeleteApiViews,
    EducationDetailApiViews,
    EducationListApiViews,
    EducationUpdateAPiViews,
    UserProfileAPIView,
    UserRegisterAPIView,
)

urlpatterns = [
    path("accounts/register/", UserRegisterAPIView.as_view(), name="register"),
    path("profile/", UserProfileAPIView.as_view(), name="profile"),
    path("education/list", EducationListApiViews.as_view(), name="educations"),
    path("education/create", EducationCreateApiViews.as_view(), name="education-create"),
    path("education/<int:id>/", EducationDetailApiViews.as_view(), name="education-deatil"),
    path("education/<int:id>/", EducationUpdateAPiViews.as_view(), name="education-update"),
    path("education/<int:id>/", EducationDeleteApiViews.as_view(), name="education-delete"),
    path("author/list", AuthorListApiViews.as_view(), name="authors"),
    path("author/create", AuthorCreateApiViews.as_view(), name="author-create"),
    path("author/<int:id>/", AuthorDetailApiViews.as_view(), name="author-deatil"),
    path("author/<int:id>/", AuthorUpdateApiViews.as_view(), name="author-update"),
    path("author/<int:id>/", AuthorDeleteApiViews.as_view(), name="author-delete"),
]
