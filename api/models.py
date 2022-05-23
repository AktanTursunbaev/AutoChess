from django.db import models
from django.contrib.auth.models import User


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    status = models.CharField(max_length=255, default="unknown")
    opponent = models.ForeignKey('Player', on_delete=models.DO_NOTHING, blank=True, null=True, related_name="opponents")
    is_opponent_clone = models.BooleanField(default=False)
    health = models.IntegerField(default=100)
    channel_name = models.CharField(max_length=255, default="")

    def __str__(self):
        return f'{self.user.username}'


class Match(models.Model):
    duration = models.TimeField(blank=True, null=True)
    players = models.ManyToManyField(Player, through="MatchInformation")

    class Meta:
        verbose_name_plural = 'Matches'

    def __str__(self):
        return f'{self.id}'


class MatchInformation(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    place = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.match.id, self.player.user.username}'
