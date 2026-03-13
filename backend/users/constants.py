"""Константы для приложения пользователей.

Содержит ограничения для длин полей, списки запрещенных имен
и настройки валидации.
"""
MAX_LENGTH_EMAIL = 254
MAX_LENGTH_NAME = 150
INVALID_USERNAMES = {
    'me', 'admin', 'root', 'administrator', 'superuser', 'super-user',
    'support', 'owner'
}
