"""Сериализаторы для работы с рецептами в различных форматах вывода."""
from django.db import transaction
from rest_framework import serializers

from core.serializers import Base64ImageField
from users.serializers import UserSerializer

from .constants import INGREDIENT_MIN_AMOUNT
from .models import Ingredient, Recipe, RecipeIngredient, Tag


class TagSerializer(serializers.ModelSerializer):
    """Сериалайзер тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер ингредиента."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Связующая модель для вывода ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Упрощенный поиск рецептов для списков избранного и корзины."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для чтения рецепта."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='ingredient_list', read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def _is_item_in_user_collection(self, obj, related_manager):
        """Проверить наличие объекта в коллекции пользователя."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return related_manager.filter(user=request.user).exists()

    def get_is_favorited(self, obj):
        """Проверить, находится ли рецепт в избранном у пользователя."""
        return self._is_item_in_user_collection(obj, obj.favorites)

    def get_is_in_shopping_cart(self, obj):
        """Проверить, находится ли рецепт в корзине покупок."""
        return self._is_item_in_user_collection(obj, obj.shopping_cart)


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Вспомогательный сериализатор для добавления ингредиентов."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(min_value=INGREDIENT_MIN_AMOUNT)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = RecipeIngredientCreateSerializer(
        many=True,
        source='recipe_ingredients'
    )
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate_ingredients(self, value):
        """Проверить список ингредиентов на пустоту и уникальность."""
        if not value:
            raise serializers.ValidationError('Нужен хотя бы один ингредиент')
        ingredients_ids = [item['ingredient'] for item in value]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться')
        return value

    def validate_tags(self, value):
        """Проверить список тегов на пустоту и отсутствие дубликатов."""
        if not value:
            raise serializers.ValidationError('Нужен хотя бы один тег')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться')
        return value

    def validate(self, data):
        """Проверить наличие изображения при создании рецепта."""
        request = self.context.get('request')

        if request.method == 'POST' and not data.get('image'):
            raise serializers.ValidationError(
                {'image': 'Это поле обязательно при создании рецепта.'}
            )
        return data

    def create_ingredients_amounts(self, ingredients, recipe):
        """Связать ингредиенты с рецептом через промежуточную модель."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                ingredient=ingredient['ingredient'],
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])

    @transaction.atomic
    def create(self, validated_data):
        """Создать новый рецепт и установить связи с тегами и ингредиентами."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amounts(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновить рецепт и пересоздать связи с тегами и ингредиентами."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        instance.tags.set(tags)
        instance.ingredient_list.all().delete()
        self.create_ingredients_amounts(ingredients, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Вернуть информацию о рецепте после создания или обновления."""
        return RecipeSerializer(instance, context=self.context).data
