from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import TagViewSet, UserViewSet

app_name = "api"
router = DefaultRouter()
router.register("tag", TagViewSet)
router.register("users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
