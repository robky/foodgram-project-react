from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models


User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField('Название', db_index=True, max_length=50)
    measurement_unit = models.CharField('Единица измерения', max_length=20)

    class Meta:
        verbose_name = "Ингридиент"
        verbose_name_plural = "Ингридиенты"

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField('Название', unique=True, max_length=100)
    color = models.CharField('Цветовой HEX-код', unique=True, max_length=7)
    slug = models.SlugField('Метка', unique=True, max_length=50)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор")
    name = models.CharField('Название', max_length=100)
    image = models.ImageField(
        'Картинка', upload_to='recipes/')  # Приходит, закодированная в Base64
    text = models.TextField('Описание')
    cooking_time = models.SmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(1, "Время приготовления не может быть меньше 1"),
        ],
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Теги"
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        ordering = ['-pub_date']
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def delete(self, *args, **kwargs):
        # До удаления записи получаем необходимую информацию
        storage, path = self.image.storage, self.image.path
        # Удаляем сначала модель (объект)
        super(Recipe, self).delete(*args, **kwargs)
        # Потом удаляем сам файл
        storage.delete(path)

    def __str__(self):
        return f'{self.name} - {self.author}'


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name="Рецепт")
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name="Ингридиенты")
    amount = models.SmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(1, "Количество не может быть меньше 1"),
        ],
    )

    class Meta:
        verbose_name = "Ингридиент в рецепте"
        verbose_name_plural = "Ингридиенты в рецепте"

    def __str__(self):
        return f'{self.recipe} - {self.ingredients}'


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name="Пользователь"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed',
        verbose_name="Автор"
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f'{self.user} - {self.author}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='voter',
        verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name="Рецепт")

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='basket_owner',
        verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name="Рецепт")

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return f'{self.user} - {self.recipe}'
