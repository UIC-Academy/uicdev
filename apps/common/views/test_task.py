from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.common.tasks import test_task


class TestTaskAPIView(GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        test_task.delay()
        return Response({"message": "Task started"})
