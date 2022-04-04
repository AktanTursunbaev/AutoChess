from django.urls import path

from .views import *

urlpatterns = [
    path('players/', PlayerList.as_view()),
    path('players/<int:pk>', PlayerDetail.as_view()),
    path('heroes/', HeroList.as_view()),
    path('heroes/<int:pk>', HeroDetail.as_view()),
    path('auth/', AuthToken.as_view()),
]
