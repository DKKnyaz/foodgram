"""Общие сериализаторы и кастомные поля для всех приложений проекта."""
import base64
import hashlib

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для обработки изображений в формате Base64."""

    def to_internal_value(self, data):
        """Преобразовать строку Base64 в объект файла.

        Декодирует входящую строку, генерирует уникальное имя файла
        через MD5-хеш и возвращает объект ContentFile. Если данные
        не являются строкой Base64, используется стандартная логика.
        """
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]

                file_name = f'{hashlib.md5(imgstr.encode()).hexdigest()}.{ext}'

                data = ContentFile(
                    base64.b64decode(imgstr),
                    name=file_name
                )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    'Некорректный формат изображения.'
                )
        return super().to_internal_value(data)
