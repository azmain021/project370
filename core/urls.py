from django.urls import path
from . import views

urlpatterns = [
    #auth routes
    path("register/", views.register_view, name="register"),

    #admin routes   
    path("", views.home, name="home"),
    path("dashboard/admin/", views.admin_dashboard, name="admin-dashboard"),
    path("dashboard/admin/payments/", views.admin_payments, name="admin-payments"),
    path("dashboard/admin/deals/", views.admin_deals, name="admin-deals"),
    path("dashboard/admin/users/", views.admin_users, name="admin-users"),
    path("dashboard/admin/users/add/", views.admin_add_user, name="admin-add-user"),
    path("dashboard/admin/properties/", views.admin_properties, name="admin-properties"),
    path("dashboard/admin/properties/add/", views.admin_add_property, name="admin-add-property"),
    path("dashboard/admin/visit-requests/", views.admin_visit_requests, name="admin-visit-requests"),
    path("dashboard/admin/bookings/", views.admin_bookings, name="admin-bookings"),
    path("redirect/", views.role_redirect, name="role-redirect"),


    #Tenant routes

    path("dashboard/tenant/", views.tenant_dashboard, name="tenant-dashboard"),
    path("dashboard/tenant/request-visit/<int:property_id>/", views.request_visit, name="request-visit"),
    path("dashboard/tenant/my-visits/", views.tenant_my_visits, name="tenant-my-visits"),
    path("dashboard/tenant/book/<int:property_id>/", views.book_property, name="book-property"),
    path("dashboard/tenant/my-bookings/", views.tenant_my_bookings, name="tenant-my-bookings"),
    path("dashboard/tenant/my-properties/", views.tenant_my_properties, name="tenant-my-properties"),
    path("dashboard/tenant/payment/<int:booking_id>/", views.initiate_payment, name="initiate-payment"),
    path("dashboard/tenant/payment/<int:booking_id>/confirmation/", views.payment_confirmation, name="payment-confirmation"),



]
