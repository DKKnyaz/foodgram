"""Сериализаторы для управления подписками и связями между пользователями.

Включает логику вывода рецептов автора в списках подписок
с поддержкой лимитирования количества записей.
"""
from rest_framework import serializers

from recipes.serializers import ShortRecipeSerializer

from .serializers import UserSerializer


class SubscriptionSerializer(UserSerializer):
    """Сериализатор для вывода подписок с рецептами."""

    recipes_count = serializers.IntegerField(read_only=True)
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = [
            *UserSerializer.Meta.fields,
            'recipes',
            'recipes_count'
        ]

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
