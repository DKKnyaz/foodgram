"""Утилиты для работы с QuerySet."""
from django.db.models import BooleanField, Exists, Value


def get_exists_annotation(user, model, **filters):
    """Генерирует Exists подзапрос, если юзер авторизован, иначе False."""
    if user.is_authenticated:
        return Exists(model.objects.filter(user=user, **filters))
    return Value(False, output_field=BooleanField())
