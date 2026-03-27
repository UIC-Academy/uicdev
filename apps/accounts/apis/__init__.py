from .serializers import AuthorSerializer, EducationSerializer
from .views import (
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
)

__all__ = [
    "EducationSerializer",
    "EducationCreateApiViews",
    "EducationDeleteApiViews",
    "EducationDetailApiViews",
    "EducationListApiViews",
    "EducationUpdateAPiViews",
    "AuthorListApiViews",
    "AuthorCreateApiViews",
    "AuthorDetailApiViews",
    "AuthorUpdateApiViews",
    "AuthorDeleteApiViews",
    "AuthorSerializer",
    "UserProfileAPIView",
]
