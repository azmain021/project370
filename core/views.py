from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone

from .models import User, Property, Booking, Payment, VisitRequest


# =========================
# HOME
# =========================

def home(request):
    return render(request, "home.html")


# =========================
# AUTH VIEWS
# =========================

def login_view(request):
    """
    Custom login for site users (ADMIN / SELLER / TENANT)
    """
    next_url = request.POST.get("next") or request.GET.get("next")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(next_url or "role-redirect")
        else:
            return render(
                request,
                "registration/login.html",
                {"error": "Invalid username or password"}
            )

    return render(request, "registration/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


def register_view(request):
    """
    Registration page for new TENANT or SELLER accounts
    """
    if request.user.is_authenticated:
        return redirect("role-redirect")

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        address = request.POST.get("address")
        role = request.POST.get("role")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Validation
        errors = []

        if not first_name or not last_name:
            errors.append("First name and last name are required.")

        if not username or not email or not password:
            errors.append("Username, email and password are required.")

        if password != confirm_password:
            errors.append("Passwords do not match.")

        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")

        if role not in ["TENANT", "SELLER"]:
            errors.append("Invalid role selected.")

        if User.objects.filter(username=username).exists():
            errors.append("Username already exists.")

        if User.objects.filter(email=email).exists():
            errors.append("Email already registered.")

        if errors:
            return render(request, "registration/register.html", {
                "errors": errors,
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "email": email,
                "phone_number": phone_number,
                "address": address,
                "role": role,
            })

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            address=address,
            role=role,
            password=password
        )

        # Auto login after registration
        login(request, user)
        return redirect("role-redirect")

    return render(request, "registration/register.html")


@login_required
def role_redirect(request):
    """
    Redirect user after login based on role
    """
    user = request.user

    if user.role == "ADMIN":
        return redirect("admin-dashboard")
    elif user.role == "SELLER":
        return redirect("seller-dashboard")
    elif user.role == "TENANT":
        return redirect("tenant-dashboard")

    return redirect("home")


# =========================
# ADMIN DASHBOARD VIEWS
# =========================

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
    pending_bookings = Booking.objects.filter(status="PENDING").count()

    context = {
        "total_users": total_users,
        "total_sellers": total_sellers,
        "total_tenants": total_tenants,
        "total_properties": total_properties,
        "total_bookings": total_bookings,
        "total_payments": total_payments,
        "pending_payments": pending_payments,
        "pending_visits": pending_visits,
        "pending_bookings": pending_bookings,
    }
    return render(request, "dashboard/admin_dashboard.html", context)


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
        image = request.FILES.get("image")  # Handle image upload

        seller = User.objects.get(id=seller_id)

        Property.objects.create(
            seller=seller,
            title=title,
            address=address,
            city=city,
            property_type=property_type,
            price=price,
            description=description,
            image=image,  # Save the image
        )

        return redirect("admin-properties")

    context = {
        "sellers": sellers,
    }
    return render(request, "dashboard/admin_add_property.html", context)


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


# =========================
# TENANT DASHBOARD
# =========================

@login_required
def tenant_dashboard(request):
    # Only TENANT can access
    if request.user.role != "TENANT":
        return redirect("home")

    # Fetch ALL properties (added by admin or seller)
    properties = Property.objects.select_related("seller").all()

    context = {
        "properties": properties,
    }

    return render(request, "dashboard/tenant_dashboard.html", context)


@login_required
def request_visit(request, property_id):
    """
    Tenant submits a visit request for a property
    """
    if request.user.role != "TENANT":
        return redirect("home")

    if request.method == "POST":
        try:
            prop = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            return redirect("tenant-dashboard")

        preferred_date = request.POST.get("preferred_date")

        # Check if tenant already has a pending request for this property
        existing = VisitRequest.objects.filter(
            property=prop,
            tenant=request.user,
            status="PENDING"
        ).exists()

        if not existing:
            VisitRequest.objects.create(
                property=prop,
                tenant=request.user,
                preferred_date=preferred_date,
                status="PENDING"
            )

        return redirect("tenant-dashboard")

    return redirect("tenant-dashboard")


@login_required
def tenant_my_visits(request):
    """
    Tenant views their visit requests
    """
    if request.user.role != "TENANT":
        return redirect("home")

    visits = VisitRequest.objects.filter(tenant=request.user).select_related(
        "property", "agent"
    ).order_by("-created_at")

    context = {
        "visits": visits,
    }

    return render(request, "dashboard/tenant_my_visits.html", context)


# =========================
# ADMIN VISIT REQUESTS
# =========================

@login_required
def admin_visit_requests(request):
    """
    Admin views and manages visit requests
    """
    if request.user.role != "ADMIN":
        return redirect("home")

    if request.method == "POST":
        visit_id = request.POST.get("visit_id")
        action = request.POST.get("action")
        agent_id = request.POST.get("agent_id")

        try:
            visit = VisitRequest.objects.get(id=visit_id)
        except VisitRequest.DoesNotExist:
            return redirect("admin-visit-requests")

        if action == "approve":
            visit.status = "APPROVED"
            if agent_id:
                try:
                    agent = User.objects.get(id=agent_id, role="AGENT")
                    visit.agent = agent
                except User.DoesNotExist:
                    pass
            visit.save()
        elif action == "reject":
            visit.status = "REJECTED"
            visit.save()

        return redirect("admin-visit-requests")

    pending_visits = VisitRequest.objects.filter(status="PENDING").select_related(
        "property", "tenant"
    ).order_by("-created_at")

    approved_visits = VisitRequest.objects.filter(status="APPROVED").select_related(
        "property", "tenant", "agent"
    ).order_by("-created_at")[:10]

    rejected_visits = VisitRequest.objects.filter(status="REJECTED").select_related(
        "property", "tenant"
    ).order_by("-created_at")[:10]

    agents = User.objects.filter(role="AGENT")

    context = {
        "pending_visits": pending_visits,
        "approved_visits": approved_visits,
        "rejected_visits": rejected_visits,
        "agents": agents,
    }

    return render(request, "dashboard/admin_visit_requests.html", context)


# =========================
# TENANT BOOKING
# =========================

@login_required
def book_property(request, property_id):
    """
    Tenant books a property after visit is approved
    """
    if request.user.role != "TENANT":
        return redirect("home")

    if request.method == "POST":
        try:
            prop = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            return redirect("tenant-my-visits")

        # Check if tenant already has a pending booking for this property
        existing = Booking.objects.filter(
            property=prop,
            tenant=request.user,
            status="PENDING"
        ).exists()

        if not existing:
            Booking.objects.create(
                property=prop,
                tenant=request.user,
                status="PENDING"
            )

        return redirect("tenant-my-bookings")

    return redirect("tenant-my-visits")


@login_required
def tenant_my_bookings(request):
    """
    Tenant views their bookings
    """
    if request.user.role != "TENANT":
        return redirect("home")

    bookings = Booking.objects.filter(tenant=request.user).select_related(
        "property", "property__seller"
    ).order_by("-created_at")

    context = {
        "bookings": bookings,
    }

    return render(request, "dashboard/tenant_my_bookings.html", context)


# =========================
# ADMIN BOOKINGS
# =========================

@login_required
def admin_bookings(request):
    """
    Admin views and manages booking requests
    """
    if request.user.role != "ADMIN":
        return redirect("home")

    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        action = request.POST.get("action")

        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return redirect("admin-bookings")

        if action == "confirm":
            booking.status = "CONFIRMED"
            # Update property status to BOOKED
            booking.property.status = "BOOKED"
            booking.property.save()
            booking.save()
        elif action == "cancel":
            booking.status = "CANCELLED"
            booking.save()

        return redirect("admin-bookings")

    pending_bookings = Booking.objects.filter(status="PENDING").select_related(
        "property", "tenant"
    ).order_by("-created_at")

    confirmed_bookings = Booking.objects.filter(status="CONFIRMED").select_related(
        "property", "tenant"
    ).order_by("-created_at")[:10]

    cancelled_bookings = Booking.objects.filter(status="CANCELLED").select_related(
        "property", "tenant"
    ).order_by("-created_at")[:10]

    context = {
        "pending_bookings": pending_bookings,
        "confirmed_bookings": confirmed_bookings,
        "cancelled_bookings": cancelled_bookings,
    }

    return render(request, "dashboard/admin_bookings.html", context)
