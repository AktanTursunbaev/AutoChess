from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'email']
        read_only_fields = ['last_login', 'date_joined']
        extra_kwargs = {'password': {'write_only': True}}


class PlayerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Player
        fields = ['user', 'rating']
        read_only_fields = ['rating']

    def create(self, validated_data):
        user = User(
            username=validated_data['user']['username'],
            email=validated_data['user']['email'],
        )
        user.set_password(validated_data['user']['password'])
        user.save()
        player = Player(
            user=user,
            rating=validated_data['rating']
        )
        player.save()
        return player
