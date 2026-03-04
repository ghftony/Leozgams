from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("parkour/", views.parkour_game, name="parkour_game"),
    path("fishing/", views.fishing_game, name="fishing_game"),
]
