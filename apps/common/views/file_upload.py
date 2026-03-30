from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import FormParser, MultiPartParser

from apps.common.models import Media
from apps.common.serializers import FileUploadSerializer


class FileUploadAPIView(CreateAPIView):
    queryset = Media.objects.all()
    serializer_class = FileUploadSerializer
    parser_classes = [FormParser, MultiPartParser]

    @extend_schema(request={"multipart/form-data": FileUploadSerializer})
    def post(self, request, *args, **kwargs):
        file = request.data.get("file")
        request.data["file"] = file

        if file.size > 10 * 1024:
            raise ValidationError({"file": "File size should be less than 10MB"})
        if file.content_type not in [
            "image/jpeg",
            "image/png",
            "image/gif",
        ]:
            raise ValidationError({"file": "File type should be image"})
        return super().post(request, *args, **kwargs)
