from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from rest_framework import filters, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.permissions import (NicePerson, NicePersonOrReadOnly,
                             PostOnlyOrAuthenticated)
from api.serializers import (CreateUserSerializer, CustomAuthTokenSerializer,
                             CustomUserSerializer, GetRecipesSerializer,
                             IngredientSerializer, SetPasswordSerializer,
                             SetRecipeSerializer, ShoppingCartSerializer,
                             TagSerializer)
from core.pdf_engine import get_shopping_cart_pdf
from foods.models import (Ingredient, IngredientRecipe, Recipe, ShoppingCart,
                          Tag)

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
    search_fields = ["^name"]


class RecipeViewSet(ModelViewSet):
    serializer_class = GetRecipesSerializer
    queryset = Recipe.objects.all()
    permission_classes = [NicePersonOrReadOnly]

    def create(self, request, *args, **kwargs):
        serializer = SetRecipeSerializer(data=request.data)
        if serializer.is_valid():
            ingredients_data = serializer.validated_data.pop("ingredients")
            tags_data = serializer.validated_data.pop("tags")
            recipe = Recipe.objects.create(
                author=request.user, **serializer.validated_data
            )
            for ingredient_data in ingredients_data:
                IngredientRecipe.objects.create(
                    recipe=recipe,
                    ingredients=ingredient_data["id"],
                    amount=ingredient_data["amount"],
                )
            for tag_data in tags_data:
                recipe.tags.add(tag_data.id)
            serializer = GetRecipesSerializer(
                instance=recipe, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        serializer = SetRecipeSerializer(data=request.data)
        if serializer.is_valid():
            ingredients_data = serializer.validated_data.pop("ingredients")
            tags_data = serializer.validated_data.pop("tags")
            recipe = get_object_or_404(Recipe, id=kwargs["pk"])
            self.check_object_permissions(self.request, recipe)
            Recipe.objects.filter(id=recipe.id).update(
                **serializer.validated_data
            )
            recipe = Recipe.objects.get(id=recipe.id)
            recipe.image = serializer.validated_data["image"]
            recipe.save()
            IngredientRecipe.objects.filter(recipe=recipe).delete()
            for ingredient_data in ingredients_data:
                IngredientRecipe.objects.create(
                    recipe=recipe,
                    ingredients=ingredient_data["id"],
                    amount=ingredient_data["amount"],
                )
            recipe.tags.through.objects.filter(recipe=recipe).delete()
            for tag_data in tags_data:
                recipe.tags.add(tag_data.id)
            serializer = GetRecipesSerializer(
                instance=recipe, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs["pk"])
        self.check_object_permissions(self.request, recipe)
        IngredientRecipe.objects.filter(recipe=recipe).delete()
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [PostOnlyOrAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateUserSerializer
        return CustomUserSerializer


# class ShoppingCartViewSet(ModelViewSet):
#     serializer_class = ShoppingCartSerializer
#     pagination_class = None
#     permission_classes = [permissions.IsAuthenticated]
#
#     def get_recipe(self):
#         recipe_id = self.kwargs.get("recipe_id")
#         return get_object_or_404(Recipe, id=recipe_id)
#
#     def get_queryset(self):
#         recipe = self.get_recipe()
#         return recipe.shopping_cart.all()
#
#     def perform_create(self, serializer):
#         recipe = self.get_recipe()
#         serializer.save(user=self.request.user, recipe=recipe)


@api_view(["POST"])
def get_token(request):
    serializer = CustomAuthTokenSerializer(data=request.data)
    if serializer.is_valid():
        user = User.objects.get(email=request.data["email"])
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {"auth_token": token.key}, status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_users_me(request):
    serializer = CustomUserSerializer(request.user)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def set_password(request):
    data = request.data
    data["user"] = request.user
    serializer = SetPasswordSerializer(data=data)
    if serializer.is_valid():
        user = request.user
        user.set_password(request.data["new_password"])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def del_token(request):
    token, _ = Token.objects.get_or_create(user=request.user)
    token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST", "DELETE"])
@permission_classes([NicePerson])
def shopping_cart(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if request.method == "POST":
        request.data["id"] = recipe.id
        serializer = ShoppingCartSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(user=request.user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == "DELETE":
        shopping_cart_recipe = get_object_or_404(
            ShoppingCart, recipe=recipe, user=request.user
        )
        shopping_cart_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([NicePerson])
def download_shopping_cart(request):
    s_cart_obj = ShoppingCart.objects.filter(user=request.user)
    result = (
        IngredientRecipe.objects.filter(recipe__in=s_cart_obj.values("recipe"))
        .select_related("ingredients")
        .values(
            name=F("ingredients__name"), mu=F("ingredients__measurement_unit")
        )
        .annotate(total=Sum("amount"))
        .order_by("name")
    )
    data = [[q["name"], q["mu"], q["total"]] for q in result]
    data.insert(0, ["Продукт", "Ед.изм.", "Кол-во"])
    return get_shopping_cart_pdf(data)
