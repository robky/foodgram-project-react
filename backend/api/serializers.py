from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueValidator

from foods.models import Tag, User


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class CustomUserSerializer(UserSerializer):
    # email = serializers.EmailField(
    #     validators=[UniqueValidator(queryset=User.objects.all())],
    #     required=True,
    #     max_length=245,
    # )
    # username = serializers.CharField(
    #     validators=[UniqueValidator(queryset=User.objects.all())],
    #     required=True,
    #     max_length=150,
    # )
    # first_name = serializers.CharField(required=True, max_length=5)
    # last_name = serializers.CharField(required=True, max_length=150)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name',)
