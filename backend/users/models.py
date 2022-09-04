from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.CharField("Электронная почта", max_length=254)
    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150)

    def is_subscribed(self):
        return self.subscribed.all().count() > 0

    def recipes_count(self):
        return self.recipes.all().count()
