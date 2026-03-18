"""Представления для управления пользователями и подписками.

Содержит эндпоинты для регистрации, аутентификации,
управления аватарами и создания подписок на авторов.
"""
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import generics, permissions, serializers, status, views
from rest_framework.response import Response

from .selectors import (
    get_annotated_authors_for_user,
    get_subscriptions_for_user,
)
from .serializers import (
    AvatarSerializer,
    SubscribeActionSerializer,
    SubscriptionSerializer,
)

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для работы с пользователями и профилем текущего пользователя."""

    http_method_names = ('get', 'post')

    def get_permissions(self):
        """Возвращает список разрешений в зависимости от действия."""
        if self.action == 'me':
            return (permissions.IsAuthenticated(),)

        if self.action == 'retrieve':
            return (permissions.AllowAny(),)

        return super().get_permissions()


class UserActionMixin:
    """Общий набор настроек для действий с пользователем."""

    permission_classes = (permissions.IsAuthenticated,)


class UserSubscriptionsView(UserActionMixin, generics.ListAPIView):
    """Список авторов, на которых подписан пользователь."""

    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        """Получение списка авторов с их рецептами."""
        return get_subscriptions_for_user(self.request.user, with_recipes=True)


class UserAvatarView(UserActionMixin, views.APIView):
    """Добавление и удаление аватара."""

    def put(self, request):
        """Добавление аватара."""
        serializer = AvatarSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        """Удаление аватара."""
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSubscribeView(UserActionMixin, views.APIView):
    """Создание и удаление подписки на автора."""

    def post(self, request, id):
        """Создание подписки."""
        author = get_object_or_404(
            get_annotated_authors_for_user(request.user, with_recipes=False),
            id=id
        )
        serializer = SubscribeActionSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Удалить подписку на автора."""
        author = get_object_or_404(User, id=id)

        deleted_count, _ = request.user.subscriptions.filter(
            author=author
        ).delete()

        if not deleted_count:
            raise serializers.ValidationError(
                {'errors': 'Вы не подписаны на этого автора.'}
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
