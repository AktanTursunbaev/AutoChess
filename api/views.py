from rest_framework import generics
from .models import *
from .serializers import *


class PlayerList(generics.ListCreateAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer


class PlayerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer


class HeroList(generics.ListCreateAPIView):
    queryset = Hero.objects.all()
    serializer_class = HeroSerializer


class HeroDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
