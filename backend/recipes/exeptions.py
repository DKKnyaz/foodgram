"""Исключения приложения recipes."""


class CSVImportError(Exception):
    """Базовое исключение для ошибок импорта CSV."""


class CSVFileNotFoundError(CSVImportError):
    """Исключение для отсутствия CSV файла."""
