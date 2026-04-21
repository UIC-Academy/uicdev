from .auth import UserDisableAPIView, UserProfileAPIView, UserRegisterAPIView, UserRegisterConfirmAPIView
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
from .profile_editing import (
    UserCertificateDetailAPIView,
    UserCertificateListCreateAPIView,
    UserEducationDetailAPIView,
    UserEducationListCreateAPIView,
    UserExperienceDetailAPIView,
    UserExperienceListCreateAPIView,
)

__all__ = [
    "UserRegisterAPIView",
    "UserRegisterConfirmAPIView",
    "UserProfileAPIView",
    "UserDisableAPIView",
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
    "UserEducationListCreateAPIView",
    "UserEducationDetailAPIView",
    "UserExperienceListCreateAPIView",
    "UserExperienceDetailAPIView",
    "UserCertificateListCreateAPIView",
    "UserCertificateDetailAPIView",
]
