"""Набор фильтров для поиска и сортировки рецептов, тегов и ингредиентов."""
from django_filters import rest_framework as filters

from .models import Ingredient, Recipe, Tag


class IngredientFilterSet(filters.FilterSet):
    """Фильтр для ингредиентов."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def _filter_by_user_relation(self, queryset, value, related_name):
        """Вспомогательный метод для фильтрации связанных сущностей."""
        if value == 1 and self.request.user.is_authenticated:
            return queryset.filter(**{
                f'{related_name}__user': self.request.user})
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        """Фильтровать рецепты по наличию в избранном у пользователя."""
        return self._filter_by_user_relation(queryset, value, 'favorites')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтровать рецепты по наличию в списке покупок у пользователя."""
        return self._filter_by_user_relation(queryset, value, 'shopping_cart')
