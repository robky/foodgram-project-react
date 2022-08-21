from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (TagViewSet, UserViewSet, get_token, get_users_me,
                       set_password, del_token)

app_name = "api"
router = DefaultRouter()
router.register("tag", TagViewSet)
router.register("users", UserViewSet)

urlpatterns = [
    path('users/me/', get_users_me),
    path('users/set_password/', set_password),
    path("", include(router.urls)),
    path('auth/token/login/', get_token),
    path('auth/token/logout/', del_token),
]
