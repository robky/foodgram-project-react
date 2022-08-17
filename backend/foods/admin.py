from django.contrib import admin

from .models import (Tag, Subscription, Recipe, Ingredient,
                     IngredientRecipe, Favorite, ShoppingCart)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'number_favorites')
    list_filter = ('author', 'name', 'tags')

    def number_favorites(self, obj):
        result = Favorite.objects.filter(recipe=obj).count()
        return result

    number_favorites.short_description = "Количество в избранном"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name', )


@admin.register(Tag, IngredientRecipe, Favorite, ShoppingCart, Subscription)
class FoodsAdmin(admin.ModelAdmin):
    pass