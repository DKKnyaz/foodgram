"""Представления для управления пользователями и подписками.

Содержит эндпоинты для регистрации, аутентификации,
управления аватарами и создания подписок на авторов.
"""
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from .models import Subscription
from .selectors import (
    get_annotated_authors_for_user,
    get_subscriptions_for_user,
)
from .serializers import AvatarSerializer
from .subscription_serializers import SubscriptionSerializer

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для работы с пользователями и профилем текущего пользователя."""
    http_method_names = ['get', 'post']

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
        """Получение списка авторов."""
        return get_subscriptions_for_user(self.request.user)


class UserAvatarView(UserActionMixin, views.APIView):
    """Добавление и удаление аватара."""

    def put(self, request):
        """Добавление аватара."""
        serializer = AvatarSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        """Удаление аватара."""
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSubscribeView(UserActionMixin, views.APIView):
    """Создание и удаление подписки на автора."""

    def post(self, request, id):
        """Создание подписки."""
        author = get_object_or_404(
            get_annotated_authors_for_user(request.user),
            id=id
        )
        if request.user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            Subscription.objects.create(user=request.user, author=author)
        except IntegrityError:
            return Response(
                {'errors': 'Вы уже подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SubscriptionSerializer(
            author, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Удалить подписку на автора."""
        author = get_object_or_404(User, id=id)
        subscription = Subscription.objects.filter(
            user=request.user, author=author
        ).first()

        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'errors': 'Вы не подписаны на этого автора'},
            status=status.HTTP_400_BAD_REQUEST
        )
