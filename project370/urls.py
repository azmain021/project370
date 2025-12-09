from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin-django/", admin.site.urls),  # optional

    # Normal login for seller + tenant
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),

    # Secret admin login
    path(
        "admin-login-370/",
        auth_views.LoginView.as_view(template_name="registration/admin_login.html"),
        name="admin-login",
    ),

    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("", include("core.urls")),
]
