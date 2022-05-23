from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task
import redis

from .models import *


@shared_task(time_limit=3)
def matchmaking():
    redis_client = redis.from_url(settings.REDIS_URL)
    queue = redis_client.hgetall(settings.REDIS_MATCHMAKING_QUEUE)
    channel_layer = get_channel_layer()
    for player_id in queue:
        groups = redis_client.hgetall(settings.REDIS_MATCHMAKING_GROUP_RATING)
        groups_rating_difference = redis_client.hgetall(settings.REDIS_MATCHMAKING_GROUP_RATING_DIFFERENCE)
        groups_size = redis_client.hgetall(settings.REDIS_MATCHMAKING_GROUP_SIZE)
        if redis_client.hexists(settings.REDIS_MATCHMAKING_GROUP_MAP, player_id) == 1:
            continue
        player = Player.objects.get(id=player_id)
        for group in groups:
            minimum_allowed_rating = int(groups[group]) - int(groups_rating_difference[group])
            maximum_allowed_rating = int(groups[group]) + int(groups_rating_difference[group])
            if minimum_allowed_rating <= player.rating <= maximum_allowed_rating:
                redis_client.hset(settings.REDIS_MATCHMAKING_GROUP_MAP, player_id, group)
                redis_client.hset(settings.REDIS_MATCHMAKING_GROUP_SIZE, group, str(int(groups_size[group]) + 1))
                break
        if redis_client.hexists(settings.REDIS_MATCHMAKING_GROUP_MAP, player_id) == 0:
            redis_client.hset(settings.REDIS_MATCHMAKING_GROUP_RATING, player_id, str(player.rating))
            redis_client.hset(
                settings.REDIS_MATCHMAKING_GROUP_RATING_DIFFERENCE,
                player_id,
                str(settings.RATING_DIFFERENCE_RANGE)
            )
            redis_client.hset(settings.REDIS_MATCHMAKING_GROUP_MAP, player_id, player_id)
            redis_client.hset(settings.REDIS_MATCHMAKING_GROUP_TIME, player_id, '0')
            redis_client.hset(settings.REDIS_MATCHMAKING_GROUP_SIZE, player_id, '1')
    groups = redis_client.hgetall(settings.REDIS_MATCHMAKING_GROUP_RATING)
    groups_rating_difference = redis_client.hgetall(settings.REDIS_MATCHMAKING_GROUP_RATING_DIFFERENCE)
    groups_size = redis_client.hgetall(settings.REDIS_MATCHMAKING_GROUP_SIZE)
    group_map = redis_client.hgetall(settings.REDIS_MATCHMAKING_GROUP_MAP)
    for group in groups:
        can_start = int(redis_client.hget(settings.REDIS_MATCHMAKING_GROUP_TIME, group)) \
                    >= settings.REDIS_MATCHMAKING_GROUP_TIMEOUT
        if groups_size[group] == b'1':
            continue
        elif groups_size[group] == b'8' or (can_start and int(groups_size[group]) >= 2):
            match_players = []
            for player_id in group_map:
                if group_map[player_id] == group:
                    match_players.append(player_id)
            match = Match.objects.create()
            for player_id in match_players:
                player = Player.objects.get(id=player_id)
                match.players.add(player)
                async_to_sync(channel_layer.send)(queue[player_id].decode('UTF-8'), {
                    "type": "return_match",
                    "match_id": match.id
                })
                redis_client.hdel(settings.REDIS_MATCHMAKING_QUEUE, player_id)
                redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_MAP, player_id)
            redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_RATING, group)
            redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_RATING_DIFFERENCE, group)
            redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_TIME, group)
            redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_SIZE, group)
        else:
            redis_client.hset(
                settings.REDIS_MATCHMAKING_GROUP_TIME,
                group,
                str(int(redis_client.hget(settings.REDIS_MATCHMAKING_GROUP_TIME, group)) + 2)
            )
            if int(groups_rating_difference[group]) < settings.MAXIMUM_RATING_DIFFERENCE_RANGE:
                redis_client.hset(
                    settings.REDIS_MATCHMAKING_GROUP_RATING_DIFFERENCE,
                    group,
                    int(groups_rating_difference[group]) + settings.RATING_EXPANSION_DELTA * 2
                )
    redis_client.close()
