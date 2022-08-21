from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.permissions import PostOnlyOrAuthenticated
from api.serializers import (TagSerializer, CustomUserSerializer,
                             CreateUserSerializer, CustomAuthTokenSerializer,
                             SetPasswordSerializer)
from foods.models import Tag


User = get_user_model()


class TagViewSet(ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [PostOnlyOrAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateUserSerializer
        return CustomUserSerializer


@api_view(['POST'])
def get_token(request):
    serializer = CustomAuthTokenSerializer(data=request.data)
    if serializer.is_valid():
        user = User.objects.get(email=request.data['email'])
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"auth_token": token.key},
                        status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_users_me(request):
    serializer = CustomUserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def set_password(request):
    data = request.data
    data['user'] = request.user
    serializer = SetPasswordSerializer(data=data)
    if serializer.is_valid():
        user = request.user
        user.set_password(request.data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def del_token(request):
    token, _ = Token.objects.get_or_create(user=request.user)
    token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)