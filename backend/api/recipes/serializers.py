"""Сериализаторы для работы с рецептами в различных форматах вывода."""
from django.db import transaction
from rest_framework import serializers

from api.core.fields import Base64ImageField
from api.core.serializers import ShortRecipeSerializer
from api.recipes.validators import validate_unique_items
from api.users.serializers import UserSerializer
from recipes.constants import INGREDIENT_MIN_AMOUNT
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


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


class RecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для чтения рецепта."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='ingredient_list', read_only=True
    )
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )


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
        queryset=Tag.objects.all(),
        many=True,
        allow_empty=False,
        validators=[validate_unique_items]
    )
    ingredients = RecipeIngredientCreateSerializer(
        many=True,
        source='recipe_ingredients',
        allow_empty=False,
        validators=[validate_unique_items]
    )
    image = Base64ImageField(required=False, allow_null=True)
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Recipe
        fields = (
            'author', 'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )

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
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                ingredient=ingredient['ingredient'],
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        """Создать новый рецепт и установить связи с тегами и ингредиентами."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        recipe = super().create(validated_data)
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


class BaseRecipeActionSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для Избранного и Корзины."""

    class Meta:
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        """Возвращает краткие данные рецепта (ShortRecipeSerializer)."""
        return ShortRecipeSerializer(
            instance.recipe,
            context=self.context
        ).data


class FavoriteSerializer(BaseRecipeActionSerializer):
    """Сериализатор для Избранного."""

    class Meta(BaseRecipeActionSerializer.Meta):
        model = Favorite
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном.'
            )
        ]


class ShoppingCartSerializer(BaseRecipeActionSerializer):
    """Сериализатор для списка покупок."""

    class Meta(BaseRecipeActionSerializer.Meta):
        model = ShoppingCart
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в списке покупок.'
            )
        ]
