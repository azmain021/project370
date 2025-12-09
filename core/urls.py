from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/admin/", views.admin_dashboard, name="admin-dashboard"),
    path("dashboard/admin/payments/", views.admin_payments, name="admin-payments"),
    path("dashboard/admin/users/", views.admin_users, name="admin-users"),
    path("dashboard/admin/users/add/", views.admin_add_user, name="admin-add-user"),
    path("dashboard/admin/properties/", views.admin_properties, name="admin-properties"),
    path("dashboard/admin/properties/add/", views.admin_add_property, name="admin-add-property"),
    path("redirect/", views.role_redirect, name="role-redirect"),






]
