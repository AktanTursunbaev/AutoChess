from django.urls import path

from .consumers import *

websocket_urlpatterns = [
    path('ws/find_match', MatchmakingQueueConsumer.as_asgi()),
    path('ws/start_match', MatchReadinessConsumer.as_asgi()),
    path('ws/play_match', MatchProcessingConsumer.as_asgi()),
]
