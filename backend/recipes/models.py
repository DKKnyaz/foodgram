"""Модели базы данных для рецептов, тегов и ингредиентов."""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.http import urlsafe_base64_encode

from .constants import (
    COOKING_MAX_TIME,
    COOKING_MIN_TIME,
    INGREDIENT_MAX_LENGTH,
    INGREDIENT_MIN_AMOUNT,
    INGREDIENT_UNIT_MAX_LENGTH,
    RECIPE_MAX_LENGTH_NAME,
    TAG_MAX_LENGTH,
)


class Tag(models.Model):
    """Модель для тегов."""

    name = models.CharField('Название', max_length=TAG_MAX_LENGTH, unique=True)
    slug = models.SlugField('Слаг', max_length=TAG_MAX_LENGTH, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель для ингредиентов."""

    name = models.CharField(
        'Название', max_length=INGREDIENT_MAX_LENGTH, db_index=True
    )
    measurement_unit = models.CharField(
        'Единицы измерения', max_length=INGREDIENT_UNIT_MAX_LENGTH
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='name_measurement_unit',
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель для рецептов."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    image = models.ImageField('Изображение', upload_to='recipes/images/')
    name = models.CharField('Название', max_length=RECIPE_MAX_LENGTH_NAME)
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                COOKING_MIN_TIME,
                f'Значение не должно быть меньше {COOKING_MIN_TIME}',
            ),
            MaxValueValidator(
                COOKING_MAX_TIME,
                f'Максимум 2 суток({COOKING_MAX_TIME}минут)'
            )
        ],
    )
    tags = models.ManyToManyField(Tag, verbose_name='Список тегов')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Список ингредиентов',
        through='RecipeIngredient'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        ordering = ('-created_at', 'name')
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name

    @property
    def short_id(self):
        """Возвращает закодированный ID для внешних ссылок."""
        return urlsafe_base64_encode(str(self.id).encode())


class RecipeIngredient(models.Model):
    """Модель связи рецепта с количеством ингридиентов."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                INGREDIENT_MIN_AMOUNT,
                f'Значение не должно быть меньше {INGREDIENT_MIN_AMOUNT}',
            ),
        ],
    )

    class Meta:
        default_related_name = 'ingredient_list'
        constraints = [
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredient_in_recipe'
            )
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.ingredient} - {self.amount}'


class UserRecipeBaseModel(models.Model):
    """Базовая модель для Избранного и Списка покупок."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_%(class)s_relation'
            )
        ]


class Favorite(UserRecipeBaseModel):
    """Модель для избранных рецептов."""

    class Meta(UserRecipeBaseModel.Meta):
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.recipe.name!r} в избранном у {self.user.username}'


class ShoppingCart(UserRecipeBaseModel):
    """Модель списка покупок для рецептов."""

    class Meta(UserRecipeBaseModel.Meta):
        default_related_name = 'shopping_cart'
        verbose_name = 'Список покупок'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'Список покупок {self.user.username} для {self.recipe.name!r}'
