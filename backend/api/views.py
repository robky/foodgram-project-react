from django.contrib.auth import get_user_model
from rest_framework import status, permissions, filters
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.permissions import PostOnlyOrAuthenticated, NicePersonOrReadOnly, \
    NicePerson
from api.serializers import (TagSerializer, CustomUserSerializer,
                             CreateUserSerializer, CustomAuthTokenSerializer,
                             SetPasswordSerializer, IngredientSerializer,
                             SetRecipeSerializer, GetRecipesSerializer)
from foods.models import Tag, Ingredient, Recipe, IngredientRecipe

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']


class RecipeViewSet(ModelViewSet):
    serializer_class = GetRecipesSerializer
    queryset = Recipe.objects.all()
    permission_classes = [NicePersonOrReadOnly]

    def create_or_update(self, request, **kwargs):
        serializer = SetRecipeSerializer(data=request.data)
        if serializer.is_valid():
            ingredients_data = serializer.validated_data.pop('ingredients')
            tags_data = serializer.validated_data.pop('tags')
            recipe = Recipe.objects.create(author=request.user,
                                           **serializer.validated_data)
            for ingredient_data in ingredients_data:
                IngredientRecipe.objects.create(
                    recipe=recipe,
                    ingredients=ingredient_data['id'],
                    amount=ingredient_data['amount'])
            for tag_data in tags_data:
                recipe.tags.add(tag_data.id)
            # recipe.save()
            serializer = GetRecipesSerializer(instance=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, **kwargs):
        return self.create_or_update(request, **kwargs)

    def update(self, request, **kwargs):
        return self.create_or_update(request, **kwargs)


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