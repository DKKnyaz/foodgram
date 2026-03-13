"""Селекторы для оптимизации запросов к базе данных в приложении пользователей.

Содержит функции для получения аннотированных данных авторов
и фильтрации списков подписок с учетом текущего пользователя.
"""
from django.db.models import Count, Exists, OuterRef, Value

from .models import Subscription, User


def get_annotated_authors_for_user(user, queryset=None):
    """Возвращает QuerySet пользователей с аннотациями подписки и рецептов.

    Добавляет поле 'is_subscribed' (Exists) для текущего пользователя
    и 'recipes_count' (Count) для отображения статистики рецептов.
    Оптимизирует запросы через prefetch_related.
    """
    if queryset is None:
        queryset = User.objects.all()

    # Аннотация подписки
    if user.is_authenticated:
        is_subscribed = Exists(
            Subscription.objects.filter(user=user, author=OuterRef('pk'))
        )
    else:
        is_subscribed = Value(False)

    return queryset.annotate(
        is_subscribed=is_subscribed,
        recipes_count=Count('recipes')
    ).prefetch_related('recipes')


def get_subscriptions_for_user(user):
    """Возвращает список авторов, на которых подписан пользователь."""
    subscribed_authors_qs = User.objects.filter(subscribers__user=user)
    return get_annotated_authors_for_user(user, queryset=subscribed_authors_qs)
