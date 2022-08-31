from drf_base64.fields import Base64ImageField
from foods.models import (Ingredient, IngredientRecipe, Recipe, ShoppingCart,
                          Tag, User)
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.validators import UniqueValidator


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
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    def get_is_subscribed(self, obj):
        return obj.subscribed.all().count() > 0

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
    name = serializers.SlugRelatedField(
        read_only=True, slug_field="name", source="ingredients"
    )
    measurement_unit = serializers.SlugRelatedField(
        read_only=True, slug_field="measurement_unit", source="ingredients"
    )

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
    image = Base64ImageField()
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
        return obj.favorite.all().count() > 0

    def get_is_in_shopping_cart(self, obj):
        return obj.shopping_cart.all().count() > 0


class ShoppingCartSerializer(ModelSerializer):
    id = serializers.SlugRelatedField(
        slug_field="id", source="recipe", read_only=True
    )
    name = serializers.SlugRelatedField(
        slug_field="name", source="recipe", read_only=True
    )
    image = serializers.SerializerMethodField()
    cooking_time = serializers.SlugRelatedField(
        slug_field="cooking_time", source="recipe", read_only=True
    )

    class Meta:
        model = ShoppingCart
        fields = ("id", "name", "image", "cooking_time")

    def validate(self, data):
        if self.context["request"].method == "POST":
            user = self.context["request"].user
            recipe_id = self.context["request"].data["id"]
            recipe = get_object_or_404(Recipe, id=recipe_id)
            if recipe.shopping_cart.filter(user=user).exists():
                raise serializers.ValidationError(
                    ["Рецепт уже есть в списке покупок"]
                )
        return data

    def get_image(self, obj):
        request = self.context.get("request")
        image_url = obj.recipe.image.url
        return request.build_absolute_uri(image_url)
