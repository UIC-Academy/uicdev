from .auth import UserProfileAPIView, UserRegisterAPIView, UserRegisterConfirmAPIView
from .author_crud import (
    AuthorCreateAPIView,
    AuthorDeleteAPIView,
    AuthorDetailAPIView,
    AuthorListAPIView,
    AuthorUpdateAPIView,
)
from .education_crud import (
    EducationCreateAPIView,
    EducationDeleteAPIView,
    EducationDetailAPIView,
    EducationListAPIView,
    EducationUpdateAPIView,
)

__all__ = [
    "UserRegisterAPIView",
    "UserRegisterConfirmAPIView",
    "UserProfileAPIView",
    "AuthorCreateAPIView",
    "AuthorDeleteAPIView",
    "AuthorDetailAPIView",
    "AuthorListAPIView",
    "AuthorUpdateAPIView",
    "EducationCreateAPIView",
    "EducationDeleteAPIView",
    "EducationDetailAPIView",
    "EducationListAPIView",
    "EducationUpdateAPIView",
]
