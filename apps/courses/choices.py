from django.db.models import TextChoices


class LessonTypeChoices(TextChoices):
    VIDEO = "video", "Video"
    AUDIO = "audio", "Audio"
    ARTICLE = "article", "Article"
    FILE = "file", "File"
    HOMEWORK = "homework", "Homework"
