"""Команда для загрузки данных из CSV-файлов в базу данных."""
import csv
from collections import namedtuple

from django.conf import settings
from django.core.management import BaseCommand
from django.db.utils import IntegrityError

from recipes.exeptions import CSVFileNotFoundError
from recipes.models import Ingredient

model_tuple = namedtuple('Model', ('file_name', 'model', 'fields'))

ingredients = model_tuple(
    'ingredients.csv',
    Ingredient,
    ('name', 'measurement_unit')
)

models = (ingredients,)


class Command(BaseCommand):
    """Менеджмент-команда для импорта CSV данных."""

    help = 'Загружает данные из csv файлов в папке data/'

    def handle(self, *args, **kwargs):
        """Обработка процесса импорта."""
        for model_data in models:
            file_path = (
                settings.BASE_DIR.parent
                / 'data'
                / model_data.file_name
            )

            try:
                file_path = open(file_path, encoding='utf-8')
            except FileNotFoundError as err:
                raise CSVFileNotFoundError(
                    f'Ошибка при импорте файла базы данных. '
                    f'Проверьте наличие файла {model_data.file_name} '
                    f'по адресу: {file_path}') from err

            with file_path:
                reader = csv.reader(file_path)

                objects_to_create = [
                    model_data.model(**dict(
                        zip(model_data.fields, row, strict=True)
                    ))
                    for row in reader if row
                ]

                try:
                    model_data.model.objects.bulk_create(objects_to_create)
                except IntegrityError:
                    self.stdout.write(self.style.WARNING(
                        f'Ошибка целостности: данные из {model_data.file_name}'
                        f'уже существуют или нарушают ограничения'
                    ))

        self.stdout.write(self.style.SUCCESS('Successfully load data'))
