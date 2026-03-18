"""Сервисный слой для получения оптимизированных данных из базы рецептов."""
from django.db.models import OuterRef, Prefetch, Sum

from api.core.querysets import get_exists_annotation
from api.users.selectors import get_annotated_authors_for_user
from recipes.models import Favorite, Recipe, RecipeIngredient, ShoppingCart


def get_recipes_with_full_data(user):
    """Возвращает QuerySet рецептов с оптимизацией N+1.

    Загружает теги, ингредиенты и аннотированных авторов.
    """
    authors_with_data = get_annotated_authors_for_user(
        user, with_recipes=False)

    return Recipe.objects.annotate(
        is_favorited=get_exists_annotation(
            user, Favorite, recipe=OuterRef('pk')
        ),
        is_in_shopping_cart=get_exists_annotation(
            user, ShoppingCart, recipe=OuterRef('pk')
        )
    ).prefetch_related(
        'tags',
        'ingredient_list__ingredient',
        Prefetch('author', queryset=authors_with_data)
    ).order_by('-created_at', 'name')


def get_shopping_cart_ingredients(user):
    """Возвращает список ингредиентов из корзины пользователя."""
    return RecipeIngredient.objects.filter(
        recipe__shopping_cart__user=user
    ).values(
        'ingredient__name',
        'ingredient__measurement_unit'
    ).annotate(
        amount=Sum('amount')
    ).order_by('ingredient__name')
