from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.apis.serializers import AuthorSerializer, EducationSerializer, UserRegisterSerializer
from apps.accounts.models import Author, Education, User


class EducationListApiViews(ListAPIView):
    queryset = Education.objects.all().order_by("name")
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]


class EducationCreateApiViews(CreateAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]


class EducationUpdateAPiViews(UpdateAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    lookup_field = "id"


class EducationDetailApiViews(RetrieveAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    lookup_field = "id"


class EducationDeleteApiViews(DestroyAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    lookup_field = "id"


class AuthorListApiViews(ListAPIView):
    queryset = Author.objects.all().order_by("first_name")
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [BasicAuthentication]


class AuthorCreateApiViews(CreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class AuthorDetailApiViews(RetrieveAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    lookup_field = "id"


class AuthorUpdateApiViews(UpdateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    lookup_field = "id"


class AuthorDeleteApiViews(DestroyAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    lookup_field = "id"


class UserRegisterAPIView(GenericAPIView):
    queryset = User.objects.filter(is_active=True, is_deleted=False)
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if User.objects.filter(phone=serializer.validated_data["phone"]).exists():
            raise ValidationError("User already exists")

        user = serializer.save()
        return Response(UserRegisterSerializer(user).data)


class UserProfileAPIView(RetrieveAPIView):
    queryset = User.objects.filter(is_active=True, is_deleted=False).select_related("avatar")
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get_object(self):
        return self.request.user
