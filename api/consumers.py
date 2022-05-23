import json
import random
import time

from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from django.db.models import Q
from asgiref.sync import async_to_sync
import redis

from .models import *
from .helpers import *


class MatchmakingQueueConsumer(WebsocketConsumer):
    def connect(self):
        redis_client = redis.from_url(settings.REDIS_URL)
        player = self.scope['user']
        player.status = 'unknown'
        player.save()
        redis_client.hset(
            settings.REDIS_MATCHMAKING_QUEUE,
            str(player.id),
            str(self.channel_name)
        )
        redis_client.close()
        self.accept()

    def disconnect(self, code):
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.hdel(settings.REDIS_MATCHMAKING_QUEUE, str(self.scope['user'].id))
        redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_RATING, str(self.scope['user'].id))
        redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_RATING_DIFFERENCE, str(self.scope['user'].id))
        redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_TIME, str(self.scope['user'].id))
        redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_SIZE, str(self.scope['user'].id))
        redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_MAP, str(self.scope['user'].id))
        group_map = redis_client.hgetall(settings.REDIS_MATCHMAKING_GROUP_MAP)
        for player_id in group_map:
            if group_map[player_id].decode('UTF-8') == str(self.scope['user'].id):
                redis_client.hdel(settings.REDIS_MATCHMAKING_GROUP_MAP, player_id)
        redis_client.close()

    def return_match(self, message):
        self.send(text_data=json.dumps({
            "match_id": message["match_id"],
        }))
        self.close()


class MatchReadinessConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self.match_id = -1
        super().__init__(*args, **kwargs)

    def connect(self):
        status = "decline"
        for header in self.scope['headers']:
            if header[0] == b'status':
                status = header[1].decode('UTF-8')
            elif header[0] == b'match-id':
                self.match_id = int(header[1].decode('UTF-8'))
        match = Match.objects.get(id=self.match_id)
        player = self.scope["user"]
        if status == "Accept":
            player.status = "accepted"
            player.save()
            self.accept()
            async_to_sync(self.channel_layer.group_add)(str(self.match_id), self.channel_name)
        elif status == "Decline":
            match.players.remove(player)
            self.close()
        self.check_match_readiness()

    def notify_about_match(self, message):
        self.send(text_data=json.dumps({
            "status": message["status"],
        }))

    def check_match_readiness(self):
        match = Match.objects.get(id=self.match_id)
        if match.players.exclude(status='unknown').count() == match.players.count():
            if match.players.filter(status='accepted').count() >= 2:
                async_to_sync(self.channel_layer.group_send)(
                    str(self.match_id),
                    {
                        "type": "notify_about_match",
                        "status": "success",
                    },
                )
            else:
                async_to_sync(self.channel_layer.group_send)(
                    str(self.match_id),
                    {
                        "type": "notify_about_match",
                        "status": "failure",
                    },
                )


class MatchProcessingConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self.match = -1
        super().__init__(*args, **kwargs)

    def connect(self):
        player = self.scope["user"]
        player.status = "connected"
        player.channel_name = self.channel_name
        player.health = 5
        player.is_opponent_clone = False
        player.save()
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.hset(settings.REDIS_LAST_ROUND, player.id, 0)
        redis_client.hset(settings.REDIS_HEALTH_DECREASED, player.id, 0)
        redis_client.close()
        self.accept()
        for header in self.scope['headers']:
            if header[0] == b'match-id':
                self.match = Match.objects.get(id=int(header[1].decode('UTF-8')))
        async_to_sync(self.channel_layer.group_add)(str(self.match), self.channel_name)
        if self.match.players.filter(status="connected").count() == self.match.players.count():
            self.assign_opponents("connected")

    def assign_opponents(self, necessary_status):
        player_pairs = random.choice(list(generate_pairs(list(self.match.players.filter(status=necessary_status)))))
        if self.match.players.filter(status=necessary_status).count() % 2 == 1:
            pair_with_clone = player_pairs.pop()
            pair_with_clone[0].status = "connected"
            pair_with_clone[0].opponent = pair_with_clone[1]
            pair_with_clone[0].is_opponent_clone = True
            pair_with_clone[0].save()
        for i in player_pairs:
            i[0].status = "connected"
            i[0].opponent = i[1]
            i[0].save()
            i[1].status = "connected"
            i[1].opponent = i[0]
            i[1].save()
        async_to_sync(self.channel_layer.group_send)(
            str(self.match),
            {
                "type": "send_notification",
                "status": "ready_to_start",
            },
        )

    def receive(self, text_data=None, bytes_data=None):
        input_data = json.loads(text_data)
        player_id = self.scope["user"].id
        player = Player.objects.get(id=player_id)
        if input_data["message_type"] == "health_decrease":
            self.process_round_end(input_data)
        elif input_data["message_type"] == "ready_for_combat":
            player.status = "ready_for_combat"
            player.save()
            ready_for_combat_players = self.match.players.filter(status="ready_for_combat").count()
            if ready_for_combat_players == self.match.players.exclude(status="finished").count():
                async_to_sync(self.channel_layer.group_send)(str(self.match),
                                                             {
                                                                 "type": "send_notification",
                                                                 "status": "ready_for_combat",
                                                             },
                                                             )
        else:
            for i in player.opponents.all():
                async_to_sync(self.channel_layer.send)(i.channel_name, {
                    "type": "process_board_change",
                    "data": input_data,
                })

    def send_notification(self, message):
        player_id = self.scope["user"].id
        player = Player.objects.get(id=player_id)
        data = {
            "status": message["status"],
            "health": player.health,
            "place": MatchInformation.objects.get(player=player, match=self.match).place or 0,
            "opponent": {
                "username": "",
                "health": 0,
                "inventory": [],
                "board": [[]],
                "is_clone": player.is_opponent_clone,
            }
        }
        if message["status"] == "ready_to_start" or message["status"] == "ready_for_combat":
            data["opponent"]["username"] = player.opponent.user.username
            data["opponent"]["health"] = player.opponent.health
        self.send(text_data=json.dumps(data))

    def process_board_change(self, message):
        input_data = message["data"]
        player_id = self.scope["user"].id
        player = Player.objects.get(id=player_id)
        data = {
            "status": "playing",
            "health": player.health,
            "place": MatchInformation.objects.get(player=player, match=self.match).place or 0,
            "opponent": {
                "username": player.opponent.user.username,
                "health": player.opponent.health,
                "inventory": input_data["hero_inventory_array"],
                "board": input_data["grid_heroes_array"],
                "is_clone": player.is_opponent_clone,
            }
        }
        data.update({"status": "playing"})
        self.send(text_data=json.dumps(data))

    def process_round_end(self, input_data):
        player_id = self.scope["user"].id
        player = Player.objects.get(id=player_id)
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.hset(settings.REDIS_LAST_ROUND, player.id, input_data["current_round"])
        redis_client.hset(settings.REDIS_HEALTH_DECREASED, player.id, input_data["health_decreased"])
        player_health_decreased = int(redis_client.hget(settings.REDIS_HEALTH_DECREASED, player.id))
        player_last_round = redis_client.hget(settings.REDIS_LAST_ROUND, player.id)
        if player.is_opponent_clone:
            if player_health_decreased > 0:
                player.health -= player_health_decreased
                player.is_opponent_clone = False
                player.save()
            self.send_round_end_details(player)
            self.check_match_end()
        else:
            opponent_health_decreased = int(redis_client.hget(settings.REDIS_HEALTH_DECREASED, player.opponent.id))
            opponent_last_round = redis_client.hget(settings.REDIS_LAST_ROUND, player.opponent.id)
            if player_last_round == opponent_last_round:
                if player_health_decreased == 0 or opponent_health_decreased == 0:
                    player.health -= player_health_decreased
                    player.opponent.health -= opponent_health_decreased
                    player.save()
                    player.opponent.save()
                self.send_round_end_details(player)
                self.send_round_end_details(player.opponent)
                self.check_match_end()
        redis_client.close()

    def send_round_end_details(self, player):
        player_id = player.id
        player = Player.objects.get(id=player_id)
        if player.health <= 0:
            status = "defeated"
            player.status = "finished"
            match_information = MatchInformation.objects.get(player=player, match=self.match)
            match_information.place = self.match.players.filter(
                Q(status="waiting_for_next_round") | Q(status="connected")
            ).count() + 1
            match_information.save()
            async_to_sync(self.channel_layer.group_discard)(str(self.match), self.channel_name)
        else:
            status = "playing"
            player.status = "waiting_for_next_round"
        player.save()
        async_to_sync(self.channel_layer.send)(player.channel_name, {
            "type": "send_notification",
            "status": status,
        })

    def check_match_end(self):
        ready_players_number = self.match.players.filter(status="waiting_for_next_round").count()
        if self.match.players.exclude(status="finished").count() == ready_players_number:
            if ready_players_number == 1:
                winner = self.match.players.get(status="waiting_for_next_round")
                async_to_sync(self.channel_layer.send)(winner.channel_name,
                                                       {
                                                           "type": "send_notification",
                                                           "status": "win",
                                                       },
                                                       )
                match_information = MatchInformation.objects.get(player=winner, match=self.match)
                match_information.place = 1
                match_information.save()
                winner.save()
                self.update_rating()
            else:
                self.assign_opponents("waiting_for_next_round")

    def update_rating(self):
        increase_place = 1
        decrease_place = self.match.players.count()
        current_change = settings.MAXIMUM_RATING_GAIN
        while increase_place < decrease_place:
            player = MatchInformation.objects.get(match=self.match, place=increase_place).player
            player.rating += current_change
            player.save()
            player = MatchInformation.objects.get(match=self.match, place=decrease_place).player
            player.rating -= current_change
            player.save()
            increase_place += 1
            decrease_place -= 1
            current_change //= 2
