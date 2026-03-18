"""Классы прав доступа для управления контентом рецептов."""
from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешить чтение всем, а изменение только автору или администратору."""

    def has_permission(self, request, view):
        """Проверить права на уровне запроса.

        Разрешает безопасные методы (GET, HEAD, OPTIONS) для всех
        пользователей и любые запросы для авторизованных.
        """
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Проверить права на уровне конкретного объекта.

        Разрешает редактирование и удаление только автору объекта
        или пользователю со статусом суперпользователя.
        """
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user
                or request.user.is_superuser)
