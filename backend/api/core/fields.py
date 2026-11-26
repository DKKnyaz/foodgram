"""
Модуль кастомных полей для Django REST Framework.

Содержит поля для обработки специфических форматов данных (например, Base64),
которые не поддерживаются стандартными средствами DRF.
"""
import base64
import binascii
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
                file_format, imgstr = data.split(';base64,')
            except (ValueError, TypeError) as err:
                raise serializers.ValidationError(
                    'Некорректный формат изображения.'
                ) from err
            
            if '/' not in file_format:
                raise serializers.ValidationError(
                    'Не указано расширение изображения.'
                )
            ext = file_format.split('/')[-1]
            
            try:
                decoded_file = base64.b64decode(imgstr)
            except (binascii.Error, TypeError) as err:
                raise serializers.ValidationError(
                    'Не удалось декодировать base64.'
                ) from err
            file_name = f'{hashlib.md5(imgstr.encode()).hexdigest()}.{ext}'
            data = ContentFile(decoded_file, name=file_name)

        return super().to_internal_value(data)
