from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from rest_framework import filters, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.permissions import (NicePerson, NicePersonOrReadOnly,
                             PostOnlyOrAuthenticated)
from api.serializers import (CreateUserSerializer, CustomAuthTokenSerializer,
                             CustomUserSerializer, FavoriteSerializer,
                             GetRecipesSerializer, IngredientSerializer,
                             SetPasswordSerializer, SetRecipeSerializer,
                             ShoppingCartSerializer, SubscriptionSerializer,
                             TagSerializer)
from core.pdf_engine import get_shopping_cart_pdf
from foods.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                          ShoppingCart, Subscription, Tag)

User = get_user_model()


class CustomSearchFilter(filters.SearchFilter):
    search_param = "name"


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    filter_backends = [CustomSearchFilter]
    search_fields = ["^name"]


class RecipeViewSet(ModelViewSet):
    serializer_class = GetRecipesSerializer
    permission_classes = [NicePersonOrReadOnly]

    def get_queryset(self):
        queryset = Recipe.objects.prefetch_related("author", "tags")
        params = self.request.query_params
        if self.request.method == "GET":
            tags = params.getlist("tags")
            if tags:
                queryset = queryset.filter(tags__slug__in=tags).distinct()
            if params.get("author"):
                author = get_object_or_404(User, id=params.get("author"))
                queryset = queryset.filter(author=author)

            if self.request.user.is_authenticated:
                if params.get("is_favorited"):
                    favorit_obj = Favorite.objects.filter(
                        user=self.request.user
                    )
                    queryset = queryset.filter(
                        id__in=favorit_obj.values("recipe_id")
                    )
                if params.get("is_in_shopping_cart"):
                    s_cart_obj = ShoppingCart.objects.filter(
                        user=self.request.user
                    )
                    queryset = queryset.filter(
                        id__in=s_cart_obj.values("recipe_id")
                    )
        return queryset

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

    @action(detail=False, methods=["get"])
    def subscriptions(self, request):
        subscriders = User.objects.filter(
            id__in=request.user.subscriber.all().values("author_id")
        )

        page = self.paginate_queryset(subscriders)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            subscriders, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[NicePerson],
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, id=pk)
        request.data["author_id"] = pk
        serializer = SubscriptionSerializer(
            data=request.data, context={"request": request}
        )
        if request.method == "POST" and serializer.is_valid():
            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(
                instance=author, context={"request": request}
            )
            return Response(serializer.data)
        if request.method == "DELETE":
            subscribe = get_object_or_404(
                Subscription, user=user, author=author
            )
            subscribe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionViewSet(ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [NicePerson]

    def get_queryset(self):
        return Subscription.objects.all(user=self.request.user)


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


@api_view(["POST", "DELETE"])
@permission_classes([NicePerson])
def favorite(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if request.method == "POST":
        request.data["id"] = recipe.id
        serializer = FavoriteSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(user=request.user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == "DELETE":
        favorite = get_object_or_404(
            Favorite, recipe=recipe, user=request.user
        )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_400_BAD_REQUEST)
