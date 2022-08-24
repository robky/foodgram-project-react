from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.validators import UniqueValidator

from foods.models import Tag, User, Ingredient, Recipe, IngredientRecipe


class CustomAuthTokenSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, )

    class Meta:
        model = User
        fields = ('email', 'password')

    def validate(self, attrs):
        user = get_object_or_404(User, email=attrs['email'])
        if not user.check_password(attrs['password']):
            raise serializers.ValidationError(
                {"password": "Неверный пароль."})
        return attrs


class CustomUserSerializer(ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    def get_is_subscribed(self, obj):
        return obj.subscribed.all().count() > 0

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed')


class CreateUserSerializer(ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        max_length=245,
    )
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        max_length=150
    )
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'password')

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'],
                                        validated_data['email'],
                                        validated_data['password'])

        user.first_name = validated_data['first_name']
        user.last_name = validated_data['last_name']
        user.save()
        return user


class SetPasswordSerializer(Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, attrs):
        user = self.initial_data['user']
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError(
                {"password": "Неверный пароль."})
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
    id = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
        source='ingredients'
    )
    name = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name',
        source='ingredients'
    )
    measurement_unit = serializers.SlugRelatedField(
        read_only=True,
        slug_field='measurement_unit',
        source='ingredients'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateRecipeSerializer(ModelSerializer):
    author = CustomUserSerializer(
        read_only=True,
    )
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        
    )
    name = serializers.CharField()
    text = serializers.CharField()
    cooking_time = serializers.IntegerField(min_value=1, )
    ingredients = IngredientRecipeSerializer(many=True, )
    # is_favorited = serializers.HiddenField(default=None)

    class Meta:
        model = Recipe
        fields = ('author', 'name', 'image', 'text', 'cooking_time', 'tags',
                  'ingredients',)
                  # 'is_favorited')

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(Ingredient, id=ingredient_data[
                'id'])
            IngredientRecipe.objects.create(recipe=recipe,
                                            ingredients=ingredient,
                                            amount=ingredient_data['amount'])
        for tag_data in tags_data:
            tag = get_object_or_404(Tag, id=tag_data)
            recipe.tags.add(tag)
        return recipe


class RecipesSerializer(CreateRecipeSerializer):
    ingredients = IngredientRecipeSerializer(many=True)
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()


    def get_is_favorited(self, obj):
        return False
