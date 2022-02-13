from django.urls import path

from .views import *

urlpatterns = [
    path('players/', PlayerList.as_view()),
    path('players/<int:pk>', PlayerDetail.as_view()),
]
