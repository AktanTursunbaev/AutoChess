from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email']
        read_only_fields = ['last_login', 'date_joined']
        extra_kwargs = {'password': {'write_only': True}}


class PlayerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Player
        fields = ['user', 'rating']

    def create(self, validated_data):
        user = User(
            username=validated_data['user']['username'],
            first_name=validated_data['user']['first_name'],
            last_name=validated_data['user']['last_name'],
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


class AbilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Ability
        exclude = ['id']


class HeroSerializer(serializers.ModelSerializer):
    abilities = AbilitySerializer(many=True, read_only=True)

    class Meta:
        model = Hero
        fields = [
            'name',
            'tier',
            'level',
            'health',
            'mana',
            'minimum_damage',
            'maximum_damage',
            'attack_speed',
            'movement_speed',
            'attack_range',
            'magic_resistance',
            'armor',
            'abilities',
        ]


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        exclude = ['id']
