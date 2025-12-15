from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import User, Property, Booking, Payment, VisitRequest
from django.utils import timezone


def home(request):
    # simple home page for now
    return render(request, "home.html")


@login_required
def admin_dashboard(request):
    # only allow ADMIN users to see this page
    if request.user.role != "ADMIN":
        return redirect("home")

    total_users = User.objects.count()
    total_sellers = User.objects.filter(role="SELLER").count()
    total_tenants = User.objects.filter(role="TENANT").count()
    total_properties = Property.objects.count()
    total_bookings = Booking.objects.count()
    total_payments = Payment.objects.count()

    pending_payments = Payment.objects.filter(status="PENDING").count()
    pending_visits = VisitRequest.objects.filter(status="PENDING").count()

    context = {
        "total_users": total_users,
        "total_sellers": total_sellers,
        "total_tenants": total_tenants,
        "total_properties": total_properties,
        "total_bookings": total_bookings,
        "total_payments": total_payments,
        "pending_payments": pending_payments,
        "pending_visits": pending_visits,
    }
    return render(request, "dashboard/admin_dashboard.html", context)

@login_required
def admin_payments(request):
    # Only admin can access this page
    if request.user.role != "ADMIN":
        return redirect("home")

    # If admin clicked "Approve" button
    if request.method == "POST":
        payment_id = request.POST.get("payment_id")
        try:
            payment = Payment.objects.get(id=payment_id, status="PENDING")
        except Payment.DoesNotExist:
            payment = None

        if payment:
            # 10% platform cut example
            payment.platform_cut = payment.amount * 0.10
            payment.seller_amount = payment.amount - payment.platform_cut

            payment.status = "APPROVED"
            payment.approved_by_admin = request.user
            payment.approved_at = timezone.now()
            payment.save()

        return redirect("admin-payments")

    # Show pending and recently approved payments
    pending_payments = Payment.objects.filter(status="PENDING").select_related(
        "booking__property",
        "booking__tenant"
    )

    approved_payments = Payment.objects.filter(status="APPROVED").order_by(
        "-approved_at"
    )[:10]

    context = {
        "pending_payments": pending_payments,
        "approved_payments": approved_payments,
    }

    return render(request, "dashboard/admin_payments.html", context)

@login_required
def admin_users(request):
    if request.user.role != "ADMIN":
        return redirect("home")

    sellers = User.objects.filter(role="SELLER")
    tenants = User.objects.filter(role="TENANT")
    agents  = User.objects.filter(role="AGENT")

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        try:
            u = User.objects.get(id=user_id)
            u.delete()
        except User.DoesNotExist:
            pass
        return redirect("admin-users")

    context = {
        "sellers": sellers,
        "tenants": tenants,
        "agents": agents,
    }

    return render(request, "dashboard/admin_users.html", context)

@login_required
def admin_add_user(request):
    if request.user.role != "ADMIN":
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone")
        role = request.POST.get("role")
        password = request.POST.get("password")

        User.objects.create_user(
            username=username,
            email=email,
            phone_number=phone_number,
            role=role,
            password=password
        )

        return redirect("admin-users")

    return render(request, "dashboard/admin_add_user.html")

@login_required
def admin_properties(request):
    if request.user.role != "ADMIN":
        return redirect("home")

    # Handle delete
    if request.method == "POST":
        prop_id = request.POST.get("property_id")
        try:
            prop = Property.objects.get(id=prop_id)
            prop.delete()
        except Property.DoesNotExist:
            pass
        return redirect("admin-properties")

    # Show all properties
    properties = Property.objects.select_related("seller").all()

    context = {
        "properties": properties,
    }
    return render(request, "dashboard/admin_properties.html", context)  

@login_required
def admin_add_property(request):
    if request.user.role != "ADMIN":
        return redirect("home")

    # list of sellers to choose from
    sellers = User.objects.filter(role="SELLER")

    if request.method == "POST":
        seller_id = request.POST.get("seller")
        title = request.POST.get("title")
        address = request.POST.get("address")
        city = request.POST.get("city")
        property_type = request.POST.get("property_type")
        price = request.POST.get("price")

        description = request.POST.get("description")

        seller = User.objects.get(id=seller_id)

        Property.objects.create(
            seller=seller,
            title=title,
            address=address,
            city=city,
            property_type=property_type,
            price=price,
            description=description,
        )

        return redirect("admin-properties")

    context = {
        "sellers": sellers,
    }
    return render(request, "dashboard/admin_add_property.html", context)

@login_required
def role_redirect(request):
    user = request.user
    if user.role == "ADMIN":
        return redirect("admin-dashboard")
    elif user.role == "SELLER":
        return redirect("seller-dashboard")
    elif user.role == "TENANT":
        return redirect("tenant-dashboard")
    return redirect("home")