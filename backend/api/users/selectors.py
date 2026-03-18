"""Селекторы для оптимизации запросов к базе данных в приложении пользователей.

Содержит функции для получения аннотированных данных авторов
и фильтрации списков подписок с учетом текущего пользователя.
"""
from django.contrib.auth import get_user_model
from django.db.models import Count, OuterRef

from api.core.querysets import get_exists_annotation
from users.models import Subscription

User = get_user_model()


def get_annotated_authors_for_user(user, queryset=None, with_recipes=False):
    """Возвращает QuerySet пользователей с аннотациями подписки и рецептов.

    Добавляет поле 'is_subscribed' (Exists) для текущего пользователя
    и 'recipes_count' (Count) для отображения статистики рецептов.
    Оптимизирует запросы через prefetch_related.
    """
    queryset = User.objects.all() if queryset is None else queryset

    queryset = queryset.annotate(
        is_subscribed=get_exists_annotation(
            user, Subscription, author=OuterRef('pk')
        ),
        recipes_count=Count('recipes')
    )

    if with_recipes:
        return queryset.prefetch_related('recipes')
    return queryset


def get_subscriptions_for_user(user, with_recipes=True):
    """Возвращает список авторов, на которых подписан пользователь."""
    subscribed_authors_qs = User.objects.filter(subscribers__user=user)
    return get_annotated_authors_for_user(
        user,
        queryset=subscribed_authors_qs,
        with_recipes=with_recipes
    )
