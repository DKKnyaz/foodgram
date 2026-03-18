"""Базовые сериализаторы для модели пользователя.

Обеспечивает преобразование данных профиля пользователя,
включая проверку статуса подписки и обработку аватаров.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.core.fields import Base64ImageField
from api.core.serializers import ShortRecipeSerializer
from users.models import Subscription

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для получения списка пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """Проверка подписки текущего пользователя на автора."""
        is_subscribed = getattr(obj, 'is_subscribed', None)
        if is_subscribed is not None:
            return bool(is_subscribed)

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        return request.user.subscriptions.filter(author=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара."""

    avatar = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SubscriptionSerializer(UserSerializer):
    """Сериализатор для вывода подписок с рецептами."""

    recipes_count = serializers.IntegerField(read_only=True)
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (
            *UserSerializer.Meta.fields,
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        """Получает рецепты автора.

        Проверяет наличие параметра 'recipes_limit' в запросе и
        обрезает QuerySet до указанного значения.
        """
        request = self.context.get('request')

        recipes = obj.recipes.all()

        if request:
            limit = request.query_params.get('recipes_limit')
            if limit and limit.isdigit():
                recipes = recipes[:int(limit)]

        return ShortRecipeSerializer(recipes, many=True, read_only=True).data


class SubscribeActionSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и валидации подписки."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого автора.'
            )
        ]

    def validate(self, data):
        """Проверить, что пользователь не подписывается на самого себя."""
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        return data

    def to_representation(self, instance):
        """Возвращает данные через SubscriptionSerializer после создания."""
        return SubscriptionSerializer(
            instance.author,
            context=self.context
        ).data
