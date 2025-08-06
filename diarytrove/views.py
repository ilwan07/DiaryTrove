from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

# Create your views here.

def index(request:HttpRequest):
    """
    The page to return when requesting the index page
    """
    return HttpResponse("Index page")
