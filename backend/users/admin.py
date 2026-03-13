from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import Subscription, User

admin.site.unregister(Group)


class BaseAdmin(admin.ModelAdmin):
    """Общий класс для регистрации моделей."""

    empty_value_display = '-пусто-'


class SubscriptionInline(admin.TabularInline):
    """Отображение подписок пользователя прямо в его профиле."""
    model = Subscription
    fk_name = 'user'
    extra = 1


@admin.register(User)
class UserAdmin(BaseUserAdmin, BaseAdmin):
    """Класс для управления пользовательской моделью в админке."""

    inlines = (SubscriptionInline,)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('avatar',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': (
            'first_name', 'last_name', 'avatar',)}),
    )

    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name', 'avatar'
    )
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser')
    list_display_links = ('id', 'username', 'email')


@admin.register(Subscription)
class SubscriptionAdmin(BaseAdmin):
    """Управление подписками."""

    list_display = ('id', 'user', 'author')
    search_fields = (
        'user__email',
        'author__email',
        'user__username',
        'author__username'
    )
    list_filter = ('user', 'author')
