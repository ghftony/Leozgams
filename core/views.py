from django.shortcuts import render, redirect
from django.views.decorators.clickjacking import xframe_options_exempt


def home(request):
    return redirect("parkour_game")


def parkour_game(request):
    return render(request, "core/parkour.html")


@xframe_options_exempt
def fishing_game(request):
    return render(request, "core/fishing.html")


def fishing_portal(request):
    return render(request, "core/fishing_portal.html")
