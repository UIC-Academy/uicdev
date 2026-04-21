from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import UserCertificate, UserEducation, UserExperience
from apps.accounts.serializers import UserCertificateSerializer, UserEducationSerializer, UserExperienceSerializer


class UserEducationListCreateAPIView(ListCreateAPIView):
    serializer_class = UserEducationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserEducation.objects.filter(user=self.request.user).select_related("education").order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserEducationDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserEducationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserEducation.objects.filter(user=self.request.user).select_related("education")


class UserExperienceListCreateAPIView(ListCreateAPIView):
    serializer_class = UserExperienceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserExperience.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserExperienceDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserExperienceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserExperience.objects.filter(user=self.request.user)


class UserCertificateListCreateAPIView(ListCreateAPIView):
    serializer_class = UserCertificateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            UserCertificate.objects.filter(user=self.request.user)
            .select_related("course", "attachment")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserCertificateDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserCertificateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserCertificate.objects.filter(user=self.request.user).select_related("course", "attachment")
