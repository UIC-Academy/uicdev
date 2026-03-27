from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView

from apps.accounts.apis import AuthorSerializer, EducationSerializer
from apps.accounts.models import Author, Education


class EducationListApiViews(ListAPIView):
    queryset = Education.objects.all().order_by("name")
    serializer_class = EducationSerializer


class EducationCreateApiViews(CreateAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer


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
