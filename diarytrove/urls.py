from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("signup/", views.auth_signup, name="signup"),
    path("login/", views.auth_login, name="login"),
    path("logout/", views.auth_logout, name="logout"),
    path("conditions/", views.conditions, name="conditions"),
    path("passwords/", views.passwords, name="passwords"),
    path("sendmail/", views.contact_email, name="contact_email"),
    path("preferences/", views.preferences, name="preferences"),
    path("home/", views.home, name="home"),
    path("gallery/", views.gallery, name="gallery"),
    path("memory/create/", views.memory_create, name="memory_create"),
    path("memory/<int:memory_pk>/", views.memory_view, name="memory_view"),
    path("memory/<int:memory_pk>/<int:media_pk>/", views.memory_media_view, name="memory_media_view"),
]
