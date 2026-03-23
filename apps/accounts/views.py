from django.shortcuts import render

from apps.accounts.models import User


def home(request):
    user = User.objects.filter(id=1).first()
    return render(request, "home.html", context={"user": user})
