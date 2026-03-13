from django.contrib import admin

from .constants import INGREDIENT_MIN_AMOUNT
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


class BaseAdmin(admin.ModelAdmin):
    """Базовая настройка для отображения пустых значений."""
    empty_value_display = '-пусто-'


class RecipeIngredientInline(admin.TabularInline):
    """Вспомогательный класс для отображения ингредиентов внутри рецепта."""
    model = RecipeIngredient
    min_num = INGREDIENT_MIN_AMOUNT
    extra = 1
    autocomplete_fields = ('ingredient',)


@admin.register(Tag)
class TagAdmin(BaseAdmin):
    """Управление тегами в админ-панели."""
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    list_editable = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(BaseAdmin):
    """Управление ингредиентами и их единицами измерения."""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Recipe)
class RecipeAdmin(BaseAdmin):
    """Управление рецептами, включая фильтрацию и просмотр ингредиентов."""
    list_display = ('id', 'name', 'author', 'get_favorites_count')
    list_filter = ('author', 'tags')
    search_fields = ('name', 'author__username', 'author__email')
    list_display_links = ('id', 'name')
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def get_favorites_count(self, obj):
        """Отображение количества добавлений в избранное."""
        return obj.favorites.count()


@admin.register(Favorite)
class FavoriteAdmin(BaseAdmin):
    """Управление избранными рецептами пользователей."""
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(BaseAdmin):
    """Управление списком покупок пользователей."""
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
