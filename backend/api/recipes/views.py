"""Представления для управления рецептами, тегами и ингредиентами."""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.views import View
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.recipes.filters import IngredientFilterSet, RecipeFilter
from api.recipes.permissions import IsAuthorOrReadOnly
from api.recipes.selectors import (
    get_recipes_with_full_data,
    get_shopping_cart_ingredients,
)
from api.recipes.validators import validate_shopping_cart_not_empty
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
)

from .serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    TagSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilterSet
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для рецептов."""

    permission_classes = (IsAuthorOrReadOnly,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        """Оптимизированный запрос с данными о подписках на авторов."""
        return get_recipes_with_full_data(self.request.user)

    def get_serializer_class(self):
        """Определяет сериализатор от метода."""
        if self.action in {'list', 'retrieve'}:
            return RecipeSerializer
        return RecipeCreateUpdateSerializer

    @action(
        methods=('post',),
        detail=True,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Добавить в избранное."""
        return self._add_to_list(FavoriteSerializer, request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Удалить из избранного."""
        return self._remove_from_list(Favorite, request, pk)

    @action(methods=('post',), detail=True)
    def shopping_cart(self, request, pk):
        """Управление корзиной покупок."""
        return self._add_to_list(ShoppingCartSerializer, request, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """Удалить из корзины."""
        return self._remove_from_list(ShoppingCart, request, pk)

    def _add_to_list(self, serializer_class, request, pk):
        """Создание связи пользователя для избранного/корзины."""
        get_object_or_404(Recipe, id=pk)

        serializer = serializer_class(
            data={'user': request.user.id, 'recipe': pk},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_list(self, model, request, pk):
        """Удаление связи пользователя для избранного/корзины."""
        get_object_or_404(Recipe, id=pk)

        deleted_count, _ = model.objects.filter(
            user=request.user,
            recipe_id=pk
        ).delete()

        if not deleted_count:
            raise serializers.ValidationError('Рецепта нет в списке.')

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Сформировать и скачать текстовый файл со списком покупок.

        Собирает все ингредиенты из рецептов в корзине пользователя,
        суммирует их количество и возвращает текстовый файл (.txt)
        в виде потока строк для оптимизации потребления памяти.
        """
        user = request.user
        validate_shopping_cart_not_empty(user)

        ingredients = get_shopping_cart_ingredients(user)

        def get_shopping_list_lines():
            yield f'Список покупок для: {user.username}\n'
            for ing in ingredients:
                name = ing['ingredient__name']
                unit = ing['ingredient__measurement_unit']
                amount = ing['amount']

                yield f'• {name} ({unit}) — {amount}\n'

        response = HttpResponse(
            get_shopping_list_lines(),
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            f'attachment; filename={user.username}_shopping_list.txt'
        )
        return response

    @action(
        detail=True,
        url_path='get-link',
        permission_classes=(permissions.AllowAny,)
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = self.get_object()
        relative_url = reverse(
            'short_link_redirect',
            kwargs={'short_id': recipe.short_id}
        )
        short_link = request.build_absolute_uri(relative_url)
        return Response({'short-link': short_link})


class RedirectShortLinkView(View):
    """Перенаправить пользователя по короткой ссылке."""

    def get(self, request, short_id):
        """Декодировать ID рецепта и выполнить редирект на фронтенд.

        Извлекает идентификатор из short_id. При успешной проверке
        существования рецепта перенаправляет на его страницу.
        В случае ошибки возвращает на главную.
        """
        try:
            recipe_id = urlsafe_base64_decode(short_id).decode()

        except (TypeError, ValueError, UnicodeDecodeError):
            return redirect('index')

        get_object_or_404(Recipe, id=recipe_id)

        target_url = reverse('recipe-frontend', kwargs={'pk': int(recipe_id)})
        return redirect(target_url)
