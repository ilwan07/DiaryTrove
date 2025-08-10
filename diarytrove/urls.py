from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("signup/", views.auth_signup, name="signup"),
    path("login/", views.auth_login, name="login"),
    path("logout/", views.auth_logout, name="logout"),
    path("conditions/", views.conditions, name="conditions"),
    path("passwords/", views.passwords, name="passwords"),
    path("preferences/", views.preferences, name="preferences"),
    path("home/", views.home, name="home"),
]
