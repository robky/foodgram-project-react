from django.contrib.auth import get_user_model
from rest_framework.viewsets import ModelViewSet

from api.serializers import (TagSerializer, CustomUserSerializer,
                             CreateUserSerializer)
from foods.models import Tag


User = get_user_model()


class TagViewSet(ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateUserSerializer
        return CustomUserSerializer
