"""Базовые сериализаторы для модели пользователя.

Обеспечивает преобразование данных профиля пользователя,
включая проверку статуса подписки и обработку аватаров.
"""
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from core.serializers import Base64ImageField

from .constants import MAX_LENGTH_NAME

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создание пользователя."""

    first_name = serializers.CharField(
        required=True, max_length=MAX_LENGTH_NAME)
    last_name = serializers.CharField(
        required=True, max_length=MAX_LENGTH_NAME)

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'email',
            'username',
            'password',
            'first_name',
            'last_name'
        )


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для получения списка пользователей."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        ]

    def get_is_subscribed(self, obj):
        """Проверка подписки текущего пользователя на автора."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False

        is_subscribed = getattr(obj, 'is_subscribed', None)
        if is_subscribed is not None:
            return bool(is_subscribed)

        return request.user.subscriptions.filter(author=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара."""

    avatar = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)
