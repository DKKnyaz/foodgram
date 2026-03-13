"""Кастомная модель пользователя и логика управления подписками."""
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q

from .constants import INVALID_USERNAMES, MAX_LENGTH_EMAIL, MAX_LENGTH_NAME


def validate_username_reserved(username):
    """Проверить имя пользователя на совпадение с резервированными.

    Сравнивает имя пользователя в нижнем регистре со списком 
    запрещенных имен INVALID_USERNAMES.
    """
    if username.lower() in INVALID_USERNAMES:
        raise ValidationError(
            'Имя пользователя "%(value)s" защищено системой.',
            params={'value': username},
            code='invalid_username',
        )


class User(AbstractUser):
    """Кастомная модель пользователя.

    Использует email как основной идентификатор для входа.
    """

    email = models.EmailField(
        'Адрес эл. почты',
        unique=True,
        max_length=MAX_LENGTH_EMAIL,
        error_messages={
            'unique': 'Пользователь с таким email уже существует.',
        },
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=MAX_LENGTH_NAME,
        unique=True,
        help_text=(
            'Обязательное поле. Не более 150 символов. '
            'Только буквы, цифры и @/./+/-/_'
        ),
        validators=[UnicodeUsernameValidator(), validate_username_reserved],
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.',
        },
    )
    first_name = models.CharField('Имя', max_length=MAX_LENGTH_NAME)
    last_name = models.CharField('Фамилия', max_length=MAX_LENGTH_NAME,)
    avatar = models.ImageField(
        'Фото профиля',
        upload_to='users/avatars/',
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return f'{self.username} ({self.email})'


class Subscription(models.Model):
    """Модель подписок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор рецепта',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                condition=~Q(user=models.F('author')),
                name='prevent_self_subscription'
            )
        ]

    def clean(self):
        """Валидация для форм и админки."""
        if self.user == self.author:
            raise ValidationError('Вы не можете подписаться на самого себя.')

    def save(self, *args, **kwargs):
        """Гарантирует запуск clean() перед сохранением в БД."""
        with transaction.atomic():
            self.full_clean()
            super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
