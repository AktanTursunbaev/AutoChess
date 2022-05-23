# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
import os

from django.conf import settings
from .celery import app as celery_app
import redis

__all__ = ('celery_app',)

redis_client = redis.from_url(settings.REDIS_URL)
for player in redis_client.hgetall(settings.REDIS_MATCHMAKING_QUEUE):
    redis_client.hdel(settings.REDIS_MATCHMAKING_QUEUE, player)

for player in redis_client.hgetall(settings.REDIS_MATCHMAKING_GROUP_MAP):
    redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_RATING, player)
    redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_RATING_DIFFERENCE, player)
    redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_TIME, player)
    redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_SIZE, player)
    redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_MAP, player)

redis_client.close()
