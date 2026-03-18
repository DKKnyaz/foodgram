"""Валидаторы для приложения рецептов."""
from collections import OrderedDict

from rest_framework import serializers
from rest_framework.exceptions import ValidationError


def validate_unique_items(value):
    """Проверка на уникальность элементов или их ID."""
    items = [
        item['id'] if isinstance(item, (dict, OrderedDict)) else item
        for item in value
    ]
    if len(items) != len(set(items)):
        raise serializers.ValidationError('Дубликаты запрещены')


def validate_shopping_cart_not_empty(user):
    """Проверить, что корзина пользователя не пуста."""
    if not user.shopping_cart.exists():
        raise ValidationError(
            'Ваша корзина пуста. Добавьте рецепты в список покупок.'
        )
