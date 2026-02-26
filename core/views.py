from django.shortcuts import render, redirect


def home(request):
    return redirect("parkour_game")


def parkour_game(request):
    return render(request, "core/parkour.html")
