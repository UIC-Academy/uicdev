from rest_framework.authentication import BasicAuthentication
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import Author
from apps.accounts.serializers import AuthorSerializer


class AuthorListAPIView(ListAPIView):
    queryset = Author.objects.all().order_by("first_name")
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [BasicAuthentication]


class AuthorCreateAPIView(CreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class AuthorDetailAPIView(RetrieveAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    lookup_field = "id"


class AuthorUpdateAPIView(UpdateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    lookup_field = "id"


class AuthorDeleteAPIView(DestroyAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    lookup_field = "id"
