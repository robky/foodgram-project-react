from django.contrib.auth import get_user_model
from rest_framework.viewsets import ModelViewSet

from api.serializers import TagSerializer, UserSerializer
from foods.models import Tag
from users.models import User


class TagViewSet(ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
