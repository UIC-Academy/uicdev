from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import Education
from apps.accounts.serializers import EducationSerializer


class EducationListAPIView(ListAPIView):
    queryset = Education.objects.all().order_by("name")
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]


class EducationCreateAPIView(CreateAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]


class EducationUpdateAPIView(UpdateAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    lookup_field = "id"


class EducationDetailAPIView(RetrieveAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    lookup_field = "id"


class EducationDeleteAPIView(DestroyAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    lookup_field = "id"
