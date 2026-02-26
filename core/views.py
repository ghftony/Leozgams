from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def home(request):
    return redirect("parkour_game")


@login_required
def parkour_game(request):
    return render(request, "core/parkour.html")
