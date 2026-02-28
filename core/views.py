from django.shortcuts import render, redirect


def home(request):
    return redirect("parkour_game")


def parkour_game(request):
    return render(request, "core/parkour.html")


def fishing_game(request):
    return render(request, "core/fishing.html")


def fishing_portal(request):
    return render(request, "core/fishing_portal.html")
