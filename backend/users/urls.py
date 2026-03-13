"""Маршрутизация эндпоинтов для приложения пользователей.

Определяет пути для управления профилем, аватарами, 
а также для работы с механизмом подписок на авторов.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    UserAvatarView,
    UserSubscribeView,
    UserSubscriptionsView,
    UserViewSet,
)

app_name = 'users'

router = DefaultRouter()

router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path(
        'users/subscriptions/',
        UserSubscriptionsView.as_view(),
        name='subscriptions'
    ),
    path('users/me/avatar/', UserAvatarView.as_view(), name='user-avatar'),
    path(
        'users/<int:id>/subscribe/',
        UserSubscribeView.as_view(),
        name='subscribe'
    ),

    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
