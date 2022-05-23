from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token

from api.models import *


@database_sync_to_async
def get_user(auth_header):
    if not auth_header:
        return AnonymousUser()
    token = Token.objects.get(key=auth_header.split()[1].decode('UTF-8'))
    player = token.user.player
    try:
        return player
    except Player.DoesNotExist:
        return AnonymousUser()


def get_auth_header(headers):
    for header in headers:
        if header[0] == b'authorization':
            return header[1]
    return ''


class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        scope['user'] = await get_user(get_auth_header(scope['headers']))

        return await self.app(scope, receive, send)
