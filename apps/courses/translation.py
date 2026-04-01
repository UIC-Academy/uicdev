from modeltranslation.translator import TranslationOptions, register

from apps.courses.models import Category


@register(Category)
class CategoryTranslation(TranslationOptions):
    fields = ("name",)
