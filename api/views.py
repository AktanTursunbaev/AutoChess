from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import *
from .serializers import *


class PlayerList(generics.ListCreateAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

    def post(self, request, *args, **kwargs):
        user = User.objects.create_user(
            username=request.POST.get('user.username'),
            first_name=request.POST.get('user.first_name'),
            last_name=request.POST.get('user.last_name'),
            email=request.POST.get('user.email'),
            password=request.POST.get('user.password')
        )
        player = Player.objects.create(user=user, rating=1000)
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'player': PlayerSerializer(player).data
        })


class PlayerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None, *args, **kwargs):
        if request.user and pk == 'me':
            return Response(PlayerSerializer(Player.objects.get(user=request.user)).data)
        return super(PlayerDetail, self).retrieve(request, pk, *args, **kwargs)


class HeroList(generics.ListCreateAPIView):
    queryset = Hero.objects.all()
    serializer_class = HeroSerializer


class HeroDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer


class AuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        player = Player.objects.get(user=user)
        return Response({
            'token': token.key,
            'player': PlayerSerializer(player).data
        })
