from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin-django/", admin.site.urls),  

    # log in for regular users  in our project (buyer /seller)
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),

    # Admin with my secret login path
    path(
        "admin-login-370/",
        auth_views.LoginView.as_view(template_name="registration/admin_login.html"),
        name="admin-login",
    ),

   
    path(
    "logout/",
    auth_views.LogoutView.as_view(
        template_name="registration/logged_out.html"
    ),
    name="logout",
),

    path("", include("core.urls")),
]
