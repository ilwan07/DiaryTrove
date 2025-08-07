from django.shortcuts import render
from django.http import HttpRequest

# Create your views here.

def index(request:HttpRequest):
    """
    The page to return when requesting the index page
    """
    return render(request, "diarytrove/index.html", {"logged_in": request.user.is_authenticated})
