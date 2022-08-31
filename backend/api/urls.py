from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (TagViewSet, UserViewSet, get_token, get_users_me,
                       set_password, del_token, IngredientViewSet,
                       RecipeViewSet, shopping_cart, download_shopping_cart)

app_name = "api"
router = DefaultRouter()
router.register("ingredients", IngredientViewSet)
router.register("recipes", RecipeViewSet, basename='recipe')
router.register("tags", TagViewSet)
router.register("users", UserViewSet)

urlpatterns = [
    path('users/me/', get_users_me),
    path('users/set_password/', set_password),
    path('recipes/<int:recipe_id>/shopping_cart/', shopping_cart),
    path('recipes/download_shopping_cart/', download_shopping_cart),
    path("", include(router.urls)),
    path('auth/token/login/', get_token),
    path('auth/token/logout/', del_token),
]
