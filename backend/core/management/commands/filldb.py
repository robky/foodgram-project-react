import os
from csv import DictReader

from django.conf import settings
from django.core.management import BaseCommand

from foods import models

DIR_CSV = os.path.join(settings.BASE_DIR, "..", "data/")

print(DIR_CSV)

IMPORTS_CSV = [
    {
        "file": "ingredients.csv",
        "model": models.Ingredient,
        "inst_fields": [],
        "add": False,
    },
]


def write_to_model(row, model, inst_fields):
    if inst_fields:
        for field in inst_fields:
            temp = field["model"].objects.get(id=row.pop(field["csv_row"]))
            row[field["field"]] = temp
    new = model(**row)
    new.save()


def write_m2m_model(row, model, parent, child):
    parent_inst = model.objects.get(id=row[parent])
    temp = child["model"].objects.get(id=row.pop(child["csv_row"]))
    getattr(parent_inst, child["field"]).add(temp)


class Command(BaseCommand):
    help = "Наполнение базы данных из csv файлов"

    def handle(self, *args, **options):
        for in_csv in IMPORTS_CSV:
            file = in_csv["file"]
            model = in_csv["model"]

            if os.path.exists(DIR_CSV + file):
                if model.objects.exists() and not in_csv["add"]:
                    print(
                        f"данные в таблице {model.__name__} уже существуют! "
                        f"Вставить записи можно только в пустую таблицу."
                    )
                    continue

                with open(DIR_CSV + file, encoding="utf-8") as csvfile:
                    reader = DictReader(csvfile, delimiter=",")
                    count = 0
                    for row in reader:
                        try:
                            if in_csv["add"]:
                                write_m2m_model(
                                    row,
                                    model,
                                    in_csv["m2m_field_parent"],
                                    in_csv["m2m_field_child"],
                                )
                            else:
                                write_to_model(row, model, in_csv["inst_fields"])
                            count += 1
                        except Exception as error:
                            print(error)
                    self.stdout.write(f"в таблицу {model.__name__} вставлено " f"{count} записей")
