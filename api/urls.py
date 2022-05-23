from django.urls import path

from .views import *

urlpatterns = [
    path('players/', PlayerList.as_view()),
    path('players/<str:pk>', PlayerDetail.as_view()),
    path('auth/', AuthToken.as_view()),
]
