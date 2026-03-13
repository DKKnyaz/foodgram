"""Представления для управления рецептами, тегами и ингредиентами."""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import urlsafe_base64_decode
from django.views import View
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import IngredientFilterSet, RecipeFilter
from .models import (
    Ingredient,
    Recipe,
    Tag,
)
from .permissions import IsAuthorOrReadOnly
from .selectors import (
    get_recipes_with_full_data,
    get_shopping_cart_ingredients,
)
from .serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    TagSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilterSet
    pagination_class = None
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для рецептов."""

    permission_classes = [IsAuthorOrReadOnly]
    filterset_class = RecipeFilter

    def get_queryset(self):
        """Оптимизированный запрос с данными о подписках на авторов."""
        return get_recipes_with_full_data(self.request.user)

    def get_serializer_class(self):
        """Определяет сериализатор от метода."""
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        """Автоматически назначает текущего пользователя автором рецепта."""
        serializer.save(author=self.request.user)

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, pk):
        """Управление избранным."""
        return self._process_relation(request.user.favorites, request, pk)

    @action(methods=['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk):
        """Управление корзиной покупок."""
        return self._process_relation(request.user.shopping_cart, request, pk)

    def _process_relation(self, manager, request, pk):
        """Универсальный метод для работы с Favorite и ShoppingCart."""
        recipe = get_object_or_404(Recipe, id=pk)
        relation = manager.filter(recipe=recipe)

        if request.method == 'POST':
            _, created = manager.get_or_create(recipe=recipe)
            if not created:
                return Response(
                    {'errors': 'Рецепт уже добавлен'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            deleted_count, _ = relation.delete()
            if not deleted_count:
                return Response(
                    {'errors': 'Рецепта нет в списке'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Сформировать и скачать текстовый файл со списком покупок.

        Собирает все ингредиенты из рецептов в корзине пользователя,
        суммирует их количество и возвращает текстовый файл (.txt)
        в виде потока строк для оптимизации потребления памяти.
        """
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

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
        methods=['get'],
        url_path='get-link',
        permission_classes=(permissions.AllowAny,)
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = self.get_object()
        short_id = recipe.short_id
        short_link = request.build_absolute_uri(f'/s/{short_id}/')
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)


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

            get_object_or_404(Recipe, id=recipe_id)

            return redirect(f'/recipes/{recipe_id}/')

        except (TypeError, ValueError, OverflowError, Recipe.DoesNotExist):
            return redirect('/')
