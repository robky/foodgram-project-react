from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Subscription, Tag)


class IngreditntsDetailsInline(admin.StackedInline):
    model = IngredientRecipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "number_favorites")
    list_filter = ("author", "name", "tags")
    inlines = [IngreditntsDetailsInline]

    def number_favorites(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    number_favorites.short_description = "Количество в избранном"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    list_filter = ("name",)


@admin.register(Tag, Favorite, ShoppingCart, Subscription)
class FoodsAdmin(admin.ModelAdmin):
    pass
