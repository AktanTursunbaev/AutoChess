from django.db import models
from django.contrib.auth.models import User


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField()


class Hero(models.Model):
    name = models.CharField(max_length=50)
    tier = models.IntegerField()
    level = models.IntegerField()
    health = models.IntegerField()
    mana = models.IntegerField()
    minimum_damage = models.IntegerField()
    maximum_damage = models.IntegerField()
    attack_speed = models.DecimalField()
    movement_speed = models.IntegerField()
    attack_range = models.IntegerField()
    magic_resistance = models.IntegerField()
    armor = models.IntegerField()


class Ability(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()


class Match(models.Model):
    duration = models.TimeField()
