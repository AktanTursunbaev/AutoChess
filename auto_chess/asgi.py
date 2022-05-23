"""
ASGI config for auto_chess project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auto_chess.settings")
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter

import api.routing
from api.middleware.channels_player_recognition import AuthMiddleware


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddleware(
        URLRouter(
            api.routing.websocket_urlpatterns
        )
    ),
})
