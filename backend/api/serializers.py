from django.utils.translation import ugettext_lazy
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.validators import UniqueValidator

from foods.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                          ShoppingCart, Tag, User)


class CustomAuthTokenSerializer(ModelSerializer):
    password = serializers.CharField(
        write_only=True,
    )

    class Meta:
        model = User
        fields = ("email", "password")

    def validate(self, attrs):
        user = get_object_or_404(User, email=attrs["email"])
        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError({"password": "Неверный пароль."})
        return attrs


class CustomUserSerializer(ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        if self.context["request"].user.is_authenticated:
            user = self.context["request"].user
            return user.subscriber.filter(author=obj).exists()
        return False


class CreateUserSerializer(ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        max_length=245,
    )
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        max_length=150,
    )
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )

    def create(self, validated_data):
        user = User.objects.create_user(
            validated_data["username"],
            validated_data["email"],
            validated_data["password"],
        )

        user.first_name = validated_data["first_name"]
        user.last_name = validated_data["last_name"]
        user.save()
        return user


class SetPasswordSerializer(Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, attrs):
        user = self.initial_data["user"]
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"password": "Неверный пароль."})
        return attrs


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"


class IngredientRecipeSerializer(ModelSerializer):
    id = serializers.SlugRelatedField(read_only=True, slug_field="id", source="ingredients")
    name = serializers.SlugRelatedField(read_only=True, slug_field="name", source="ingredients")
    measurement_unit = serializers.SlugRelatedField(read_only=True, slug_field="measurement_unit", source="ingredients")

    class Meta:
        model = IngredientRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class CreateIngredientRecipeSerializer(ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )

    class Meta:
        model = IngredientRecipe
        fields = ("id", "amount")


class BaseRecipeSerializer(ModelSerializer):
    name = serializers.CharField()
    text = serializers.CharField()
    cooking_time = serializers.IntegerField(
        min_value=1,
    )


class SetRecipeSerializer(BaseRecipeSerializer):
    image = Base64ImageField(required=False)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    ingredients = CreateIngredientRecipeSerializer(
        many=True,
    )

    class Meta:
        model = Recipe
        fields = (
            "name",
            "image",
            "text",
            "cooking_time",
            "tags",
            "ingredients",
        )

    def validate(self, data):
        if self.context["request"].method == "POST" and not data.get('image'):
            raise serializers.ValidationError(
                {'image': ugettext_lazy('Ни одного файла не было отправлено.')})
        return data


class GetRecipesSerializer(BaseRecipeSerializer):
    image = serializers.SerializerMethodField()
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(many=True)
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "name",
            "image",
            "text",
            "cooking_time",
            "tags",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def get_image(self, obj):
        request = self.context.get("request")
        image_url = obj.image.url
        return request.build_absolute_uri(image_url)

    def get_is_favorited(self, obj):
        if self.context["request"].user.is_authenticated:
            user = self.context["request"].user
            return user.voter.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        if self.context["request"].user.is_authenticated:
            user = self.context["request"].user
            return user.basket_owner.filter(recipe=obj).exists()
        return False


class GeneralSerializer(ModelSerializer):
    id = serializers.SlugRelatedField(slug_field="id", source="recipe", read_only=True)
    name = serializers.SlugRelatedField(slug_field="name", source="recipe", read_only=True)
    image = serializers.SerializerMethodField()
    cooking_time = serializers.SlugRelatedField(slug_field="cooking_time", source="recipe", read_only=True)

    def get_image(self, obj):
        request = self.context.get("request")
        image_url = obj.recipe.image.url
        return request.build_absolute_uri(image_url)


class ShoppingCartSerializer(GeneralSerializer):
    class Meta:
        model = ShoppingCart
        fields = ("id", "name", "image", "cooking_time")

    def validate(self, data):
        if self.context["request"].method == "POST":
            user = self.context["request"].user
            recipe_id = self.context["request"].data["id"]
            recipe = get_object_or_404(Recipe, id=recipe_id)
            if recipe.shopping_cart.filter(user=user).exists():
                raise serializers.ValidationError(["Рецепт уже есть в списке покупок"])
        return data


class FavoriteSerializer(GeneralSerializer):
    class Meta:
        model = Favorite
        fields = ("id", "name", "image", "cooking_time")

    def validate(self, data):
        if self.context["request"].method == "POST":
            user = self.context["request"].user
            recipe_id = self.context["request"].data["id"]
            recipe = get_object_or_404(Recipe, id=recipe_id)
            if recipe.favorite.filter(user=user).exists():
                raise serializers.ValidationError(["Рецепт уже есть в избранном"])
        return data


class LimitedListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        limit = self.context["request"].query_params.get("recipes_limit")
        if limit:
            data = data.all()[: int(limit)]
        return super(LimitedListSerializer, self).to_representation(data)


class SubscribeRecipeSerializer(ModelSerializer):
    class Meta:
        list_serializer_class = LimitedListSerializer
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class SubscriptionSerializer(CustomUserSerializer):
    email = serializers.StringRelatedField()
    username = serializers.StringRelatedField()
    first_name = serializers.StringRelatedField()
    last_name = serializers.StringRelatedField()
    recipes = SubscribeRecipeSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def validate(self, data):
        if self.context["request"].method == "POST":
            user = self.context["request"].user
            author_id = self.context["request"].data["author_id"]
            author = get_object_or_404(User, id=author_id)
            if user == author:
                raise serializers.ValidationError(["Нельзя подписаться на самого себя"])
            if author.subscribed.filter(user=user).exists():
                raise serializers.ValidationError(["Вы уже подписаны на этого автора"])
        return data
