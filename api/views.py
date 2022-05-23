from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.utils import IntegrityError

from .models import *
from .serializers import *


class PlayerList(generics.ListCreateAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

    def post(self, request, *args, **kwargs):
        try:
            if request.POST:
                user = User.objects.create_user(
                    username=request.POST.get('user.username'),
                    email=request.POST.get('user.email'),
                    password=request.POST.get('user.password')
                )
            else:
                user = User.objects.create_user(
                    username=request.data.get('user').get('username'),
                    email=request.data.get('user').get('email'),
                    password=request.data.get('user').get('password')
                )
        except IntegrityError as e:
            return Response({
                'message': str(e.__cause__)
            }, status=400)
        player = Player.objects.create(user=user, rating=1000)
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'player': PlayerSerializer(player).data
        })


class PlayerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

    def retrieve(self, request, pk=None, *args, **kwargs):
        if request.user and pk == 'me':
            return Response(PlayerSerializer(Player.objects.get(user=request.user)).data)
        return super(PlayerDetail, self).retrieve(request, pk, *args, **kwargs)


class AuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'player': PlayerSerializer(user.player).data
        })
