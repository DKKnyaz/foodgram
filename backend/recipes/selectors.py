"""Сервисный слой для получения оптимизированных данных из базы рецептов."""
from django.db.models import Prefetch, Sum

from users.selectors import get_annotated_authors_for_user

from .models import Recipe, RecipeIngredient


def get_recipes_with_full_data(user):
    """Возвращает QuerySet рецептов с оптимизацией N+1.

    Загружает теги, ингредиенты и аннотированных авторов.
    """
    authors_with_data = get_annotated_authors_for_user(user)

    return Recipe.objects.select_related('author').prefetch_related(
        'tags',
        'ingredient_list__ingredient',
        Prefetch('author', queryset=authors_with_data)
    )


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
