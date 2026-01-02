from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum

from .models import User, Property, Booking, Payment, VisitRequest, PropertyImage


# home - displays featured properties
def home(request):
    # Get all featured properties (no limit - admin can feature as many as they want)
    featured_properties = list(Property.objects.filter(is_featured=True, status="AVAILABLE"))
    
    return render(request, "home.html", {"featured_properties": featured_properties})


# auth routes - shared by all users

# login - authenticates user and redirects based on role
def login_view(request):
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


# logout - logs out user and redirects to login
def logout_view(request):
    logout(request)
    return redirect("login")


# register - creates new tenant or seller account
def register_view(request):
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


# role_redirect - sends user to correct dashboard based on role
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


# admin routes - made by azmain

# admin_dashboard - shows overview stats for admin
@login_required
def admin_dashboard(request):
    if request.user.role != "ADMIN":
        return redirect("home")

    total_users = User.objects.count()
    total_sellers = User.objects.filter(role="SELLER").count()
    total_tenants = User.objects.filter(role="TENANT").count()
    total_properties = Property.objects.count()
    total_bookings = Booking.objects.count()
    total_payments = Payment.objects.count()
    completed_deals = Payment.objects.filter(seller_amount_sent=True).count()

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
        "completed_deals": completed_deals,
        "pending_payments": pending_payments,
        "pending_visits": pending_visits,
        "pending_bookings": pending_bookings,
    }
    return render(request, "dashboard/admin_dashboard.html", context)


# admin_users - lists all users, allows deletion
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


# admin_add_user - creates new user account
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


# admin_properties - lists all properties, toggle featured, delete
@login_required
def admin_properties(request):
    if request.user.role != "ADMIN":
        return redirect("home")

    # Handle POST actions
    if request.method == "POST":
        prop_id = request.POST.get("property_id")
        action = request.POST.get("action", "delete")
        
        try:
            prop = Property.objects.get(id=prop_id)
            
            if action == "toggle_featured":
                # Only allow featuring if property is not SOLD
                if prop.status != "SOLD":
                    prop.is_featured = not prop.is_featured
                    prop.save()
            elif action == "delete":
                prop.delete()
                
        except Property.DoesNotExist:
            pass
        return redirect("admin-properties")

    # Show all properties
    properties = list(Property.objects.select_related("seller").all())

    context = {
        "properties": properties,
    }
    return render(request, "dashboard/admin_properties.html", context)


# admin_add_property - creates new property for a seller
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

        prop = Property.objects.create(
            seller=seller,
            title=title,
            address=address,
            city=city,
            property_type=property_type,
            price=price,
            description=description,
        )

        # Handle multiple images
        images = request.FILES.getlist("images")
        for img in images:
            PropertyImage.objects.create(property=prop, image=img)

        return redirect("admin-properties")

    context = {
        "sellers": sellers,
    }
    return render(request, "dashboard/admin_add_property.html", context)


# admin_payments - approves payments and sends to seller
@login_required
def admin_payments(request):
    if request.user.role != "ADMIN":
        return redirect("home")

    # If admin clicked "Approve" button or "Send to Seller" button
    if request.method == "POST":
        action = request.POST.get("action")
        payment_id = request.POST.get("payment_id")
        
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            payment = None

        if payment:
            if action == "approve":
                # Only approve if currently pending
                if payment.status == "PENDING":
                    # 10% platform cut example
                    payment.platform_cut = payment.amount * Decimal('0.10')
                    payment.seller_amount = payment.amount - payment.platform_cut

                    payment.status = "APPROVED"
                    payment.approved_by_admin = request.user
                    payment.approved_at = timezone.now()
                    
                    # Mark property as BOOKED (sold) if it's a SELL property
                    if payment.booking.property.property_type == "SELL":
                        payment.booking.property.status = "BOOKED"
                        payment.booking.property.save()
                    
                    payment.save()
            
            elif action == "send_to_seller":
                # Only send if approved and not already sent
                if payment.status == "APPROVED" and not payment.seller_amount_sent:
                    payment.seller_amount_sent = True
                    payment.seller_amount_sent_at = timezone.now()
                    payment.save()

        return redirect("admin-payments")

    # Show pending and recently approved payments
    pending_payments = Payment.objects.filter(status="PENDING").select_related(
        "booking__property",
        "booking__tenant"
    )

    approved_payments = Payment.objects.filter(status="APPROVED").order_by(
        "-approved_at"
    ).select_related(
        "booking__property",
        "booking__tenant",
        "approved_by_admin"
    )

    # Calculate total platform cuts for all approved payments
    total_platform_cut = sum(p.platform_cut for p in approved_payments)

    context = {
        "pending_payments": pending_payments,
        "approved_payments": approved_payments,
        "total_platform_cut": total_platform_cut,
    }

    return render(request, "dashboard/admin_payments.html", context)


# admin_deals - shows completed transactions where seller received payment
def admin_deals(request):
    if request.user.role != "ADMIN":
        return redirect("home")

    # Get all completed deals (payments where seller amount has been sent)
    completed_deals = Payment.objects.filter(
        seller_amount_sent=True
    ).select_related(
        "booking__property__seller",
        "booking__tenant",
        "approved_by_admin"
    ).order_by("-seller_amount_sent_at")

    context = {
        "completed_deals": completed_deals,
    }

    return render(request, "dashboard/admin_deals.html", context)


# tenant routes - made by tanzeem

# property_detail - shows property with all images and booking options
@login_required
def property_detail(request, property_id):
    if request.user.role != "TENANT":
        return redirect("home")

    prop = get_object_or_404(Property, id=property_id)
    images = prop.images.all()

    # Check if tenant already has a pending visit request
    has_pending_visit = VisitRequest.objects.filter(
        property=prop,
        tenant=request.user,
        status="PENDING"
    ).exists()

    # Check if tenant has an approved visit
    has_approved_visit = VisitRequest.objects.filter(
        property=prop,
        tenant=request.user,
        status="APPROVED"
    ).exists()

    # Check if tenant already has a booking for this property
    has_booking = Booking.objects.filter(
        property=prop,
        tenant=request.user,
        status__in=["PENDING", "CONFIRMED", "COMPLETED"]
    ).exists()

    context = {
        "property": prop,
        "images": images,
        "has_pending_visit": has_pending_visit,
        "has_approved_visit": has_approved_visit,
        "has_booking": has_booking,
    }

    return render(request, "dashboard/property_detail.html", context)


# tenant_dashboard - shows available properties for tenant
@login_required
def tenant_dashboard(request):
    if request.user.role != "TENANT":
        return redirect("home")

    # Fetch available properties only (exclude BOOKED/SOLD properties)
    properties = Property.objects.select_related("seller").filter(status="AVAILABLE")

    # Count confirmed/purchased properties (completed bookings with approved payments)
    confirmed_properties_count = Booking.objects.filter(
        tenant=request.user,
        status="COMPLETED",
        payments__status="APPROVED"
    ).distinct().count()

    context = {
        "properties": properties,
        "confirmed_properties_count": confirmed_properties_count,
    }

    return render(request, "dashboard/tenant_dashboard.html", context)


# request_visit - tenant submits visit request for property
@login_required
def request_visit(request, property_id):
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


# tenant_my_visits - shows tenant's visit requests
@login_required
def tenant_my_visits(request):
    if request.user.role != "TENANT":
        return redirect("home")

    # Get property IDs where tenant has completed payment (COMPLETED bookings)
    completed_property_ids = set(
        Booking.objects.filter(
            tenant=request.user,
            status="COMPLETED"
        ).values_list("property_id", flat=True)
    )

    # Exclude visits for properties that have been paid/completed
    visits = VisitRequest.objects.filter(tenant=request.user).exclude(
        property_id__in=completed_property_ids
    ).select_related(
        "property", "agent"
    ).order_by("-created_at")

    # Get property IDs that tenant has already booked (PENDING or CONFIRMED)
    booked_property_ids = set(
        Booking.objects.filter(
            tenant=request.user,
            status__in=["PENDING", "CONFIRMED"]
        ).values_list("property_id", flat=True)
    )

    # Get property IDs that are already confirmed by anyone
    confirmed_property_ids = set(
        Booking.objects.filter(status="CONFIRMED").values_list("property_id", flat=True)
    )

    # Add a flag to each visit indicating if booking is allowed
    for visit in visits:
        visit.can_book = (
            visit.status == "APPROVED" and
            visit.property_id not in booked_property_ids and
            visit.property_id not in confirmed_property_ids
        )
        visit.already_booked = visit.property_id in booked_property_ids
        visit.property_confirmed = visit.property_id in confirmed_property_ids

    context = {
        "visits": visits,
    }

    return render(request, "dashboard/tenant_my_visits.html", context)


# admin_visit_requests - admin approves/rejects visit requests, assigns agents
@login_required
def admin_visit_requests(request):
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


# book_property - tenant books property after visit approved
@login_required
def book_property(request, property_id):
    if request.user.role != "TENANT":
        return redirect("home")

    if request.method == "POST":
        try:
            prop = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            return redirect("tenant-my-visits")

        # Check if tenant already has an active booking (PENDING or CONFIRMED) for this property
        existing = Booking.objects.filter(
            property=prop,
            tenant=request.user,
            status__in=["PENDING", "CONFIRMED"]
        ).exists()

        # Also check if property is already booked by someone else
        property_booked = Booking.objects.filter(
            property=prop,
            status="CONFIRMED"
        ).exists()

        if not existing and not property_booked:
            Booking.objects.create(
                property=prop,
                tenant=request.user,
                status="PENDING"
            )

        return redirect("tenant-my-bookings")

    return redirect("tenant-my-visits")


# tenant_my_bookings - shows tenant's pending and confirmed bookings
@login_required
def tenant_my_bookings(request):
    if request.user.role != "TENANT":
        return redirect("home")

    # Exclude COMPLETED bookings - those are shown in "My Properties"
    bookings = Booking.objects.filter(tenant=request.user).exclude(
        status="COMPLETED"
    ).select_related(
        "property", "property__seller"
    ).order_by("-created_at")

    context = {
        "bookings": bookings,
    }

    return render(request, "dashboard/tenant_my_bookings.html", context)


# tenant_my_properties - shows tenant's purchased properties
@login_required
def tenant_my_properties(request):
    if request.user.role != "TENANT":
        return redirect("home")

    # Get all completed bookings with approved payments
    completed_bookings = Booking.objects.filter(
        tenant=request.user,
        status="COMPLETED"
    ).select_related("property", "property__seller").prefetch_related("payments")

    # Build list of paid properties with payment info
    paid_properties = []
    for booking in completed_bookings:
        payment = booking.payments.filter(status="APPROVED").first()
        if payment:
            paid_properties.append({
                "property": booking.property,
                "payment": payment,
                "booking": booking,
            })

    context = {
        "paid_properties": paid_properties,
    }

    return render(request, "dashboard/tenant_my_properties.html", context)


# admin_bookings - admin confirms or cancels booking requests
@login_required
def admin_bookings(request):
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


# initiate_payment - tenant pays for confirmed booking, marks property as sold
@login_required
def initiate_payment(request, booking_id):
    if request.user.role != "TENANT":
        return redirect("home")

    try:
        booking = Booking.objects.get(id=booking_id, tenant=request.user, status="CONFIRMED")
    except Booking.DoesNotExist:
        return redirect("tenant-my-bookings")

    # Check if payment already exists for this booking
    existing_payment = Payment.objects.filter(booking=booking).exists()
    
    if not existing_payment:
        # Calculate platform cut (10%) and seller amount
        amount = booking.property.price
        platform_cut = amount * Decimal('0.10')
        seller_amount = amount - platform_cut
        
        # Create payment record - auto-approved (no admin approval needed)
        Payment.objects.create(
            booking=booking,
            amount=amount,
            platform_cut=platform_cut,
            seller_amount=seller_amount,
            status="APPROVED",
            approved_at=timezone.now()
        )
        
        # Mark booking as COMPLETED (so Pay Now button disappears)
        booking.status = "COMPLETED"
        booking.save()
        
        # Mark property as SOLD and remove from featured
        booking.property.status = "SOLD"
        booking.property.is_featured = False
        booking.property.save()

    return redirect("payment-confirmation", booking_id=booking_id)


# payment_confirmation - shows payment success page
@login_required
def payment_confirmation(request, booking_id):
    if request.user.role != "TENANT":
        return redirect("home")

    try:
        booking = Booking.objects.get(id=booking_id, tenant=request.user)
        payment = Payment.objects.get(booking=booking)
    except (Booking.DoesNotExist, Payment.DoesNotExist):
        return redirect("tenant-my-bookings")

    context = {
        "booking": booking,
        "payment": payment,
    }

    return render(request, "dashboard/payment_confirmation.html", context)


# seller routes - made by saud

# seller_dashboard - shows seller stats, properties, bookings, payments
@login_required
def seller_dashboard(request):
    if request.user.role != "SELLER":
        return redirect("home")

    seller = request.user
    properties = Property.objects.filter(seller=seller).order_by("-created_at")
    
    # Get bookings for seller's properties
    bookings = Booking.objects.filter(property__seller=seller).select_related(
        "property", "tenant"
    ).order_by("-created_at")
    
    # Get appointments (visit requests) for seller's properties
    appointments = VisitRequest.objects.filter(property__seller=seller).select_related(
        "property", "tenant"
    ).order_by("-created_at")
    
    # Only count payments that admin has sent to seller (seller_amount_sent=True)
    payments_sent = Payment.objects.filter(
        booking__property__seller=seller,
        status="APPROVED",
        seller_amount_sent=True
    )
    payments_total = payments_sent.aggregate(Sum("seller_amount"))["seller_amount__sum"] or 0
    
    # Pending payments (approved by admin but not yet sent to seller)
    pending_payments = Payment.objects.filter(
        booking__property__seller=seller,
        status="APPROVED",
        seller_amount_sent=False
    ).aggregate(Sum("seller_amount"))["seller_amount__sum"] or 0

    context = {
        "properties": properties,
        "bookings": bookings,
        "appointments": appointments,
        "payments_total": payments_total,
        "pending_payments": pending_payments,
    }
    return render(request, "dashboard/seller_dashboard.html", context)


# seller_properties - lists seller's properties
@login_required
def seller_properties(request):
    if request.user.role != "SELLER":
        return redirect("home")

    properties = Property.objects.filter(seller=request.user).order_by("-created_at")

    context = {"properties": properties}
    return render(request, "dashboard/seller_properties.html", context)


# add_property - seller creates new property listing
@login_required
def add_property(request):
    if request.user.role != "SELLER":
        return redirect("home")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        address = request.POST.get("address")
        city = request.POST.get("city")
        price = request.POST.get("price")
        property_type = request.POST.get("property_type")
        is_featured = True if request.POST.get("is_featured") == "on" else False

        prop = Property.objects.create(
            title=title,
            description=description,
            address=address,
            city=city,
            price=price,
            property_type=property_type,
            is_featured=is_featured,
            seller=request.user,
        )

        images = request.FILES.getlist("images")
        for img in images:
            PropertyImage.objects.create(property=prop, image=img)

        return redirect("seller_properties")

    return render(request, "dashboard/seller_add_property.html")


# edit_property - seller updates property details and images
@login_required
def edit_property(request, property_id):
    prop = get_object_or_404(Property, id=property_id, seller=request.user)

    if request.method == "POST":
        prop.title = request.POST.get("title")
        prop.description = request.POST.get("description")
        prop.address = request.POST.get("address")
        prop.city = request.POST.get("city")
        prop.price = request.POST.get("price")
        prop.property_type = request.POST.get("property_type")
        prop.is_featured = True if request.POST.get("is_featured") == "on" else False
        prop.save()

        # Add new images
        images = request.FILES.getlist("images")
        for img in images:
            PropertyImage.objects.create(property=prop, image=img)

        # Delete selected images
        delete_images = request.POST.getlist("delete_images")
        if delete_images:
            PropertyImage.objects.filter(id__in=delete_images, property=prop).delete()

        return redirect("seller_properties")

    context = {
        "property": prop,
        "images": prop.images.all(),
    }
    return render(request, "dashboard/seller_add_property.html", context)


# delete_property - seller removes property listing
@login_required
def delete_property(request, property_id):
    prop = get_object_or_404(Property, id=property_id, seller=request.user)
    if request.method == "POST":
        prop.delete()
    return redirect("seller_properties")


# seller_appointments - shows visit requests for seller's properties
@login_required
def seller_appointments(request):
    if request.user.role != "SELLER":
        return redirect("home")

    properties = Property.objects.filter(seller=request.user)
    appointments = VisitRequest.objects.filter(property__in=properties).select_related(
        "property", "tenant", "agent"
    ).order_by("-created_at")

    context = {"appointments": appointments}
    return render(request, "dashboard/seller_appointments.html", context)


# seller_bookings - shows bookings for seller's properties
@login_required
def seller_bookings(request):
    if request.user.role != "SELLER":
        return redirect("home")

    properties = Property.objects.filter(seller=request.user)
    bookings = Booking.objects.filter(property__in=properties).select_related(
        "property", "tenant"
    ).order_by("-created_at")

    context = {"bookings": bookings}
    return render(request, "dashboard/seller_bookings.html", context)


# seller_payments - shows received and pending payments for seller
@login_required
def seller_payments(request):
    if request.user.role != "SELLER":
        return redirect("home")

    # Only show payments that admin has approved AND sent to seller
    payments = Payment.objects.filter(
        booking__property__seller=request.user,
        status="APPROVED",
        seller_amount_sent=True
    ).select_related(
        "booking", "booking__property", "booking__tenant"
    ).order_by("-seller_amount_sent_at")
    
    # Also get pending payments (approved but not sent yet) for info
    pending_payments = Payment.objects.filter(
        booking__property__seller=request.user,
        status="APPROVED",
        seller_amount_sent=False
    ).select_related(
        "booking", "booking__property", "booking__tenant"
    ).order_by("-approved_at")

    context = {
        "payments": payments,
        "pending_payments": pending_payments,
    }
    return render(request, "dashboard/seller_payments.html", context)



"""
================================================================================
SQL EQUIVALENT QUERIES
================================================================================

ADMIN ROUTES - made by azmain
================================================================================

admin_dashboard - shows overview stats for admin

User.objects.count()
SELECT COUNT(*) FROM core_user;

User.objects.filter(role="SELLER").count()
SELECT COUNT(*) FROM core_user WHERE role = 'SELLER';

User.objects.filter(role="TENANT").count()
SELECT COUNT(*) FROM core_user WHERE role = 'TENANT';

Property.objects.count()
SELECT COUNT(*) FROM core_property;

Booking.objects.count()
SELECT COUNT(*) FROM core_booking;

Payment.objects.count()
SELECT COUNT(*) FROM core_payment;

Payment.objects.filter(seller_amount_sent=True).count()
SELECT COUNT(*) FROM core_payment WHERE seller_amount_sent = TRUE;

Payment.objects.filter(status="PENDING").count()
SELECT COUNT(*) FROM core_payment WHERE status = 'PENDING';

VisitRequest.objects.filter(status="PENDING").count()
SELECT COUNT(*) FROM core_visitrequest WHERE status = 'PENDING';

Booking.objects.filter(status="PENDING").count()
SELECT COUNT(*) FROM core_booking WHERE status = 'PENDING';


admin_users - lists all users, allows deletion

User.objects.filter(role="SELLER")
SELECT * FROM core_user WHERE role = 'SELLER';

User.objects.filter(role="TENANT")
SELECT * FROM core_user WHERE role = 'TENANT';

User.objects.filter(role="AGENT")
SELECT * FROM core_user WHERE role = 'AGENT';

User.objects.get(id=user_id)
SELECT * FROM core_user WHERE id = user_id;

u.delete()
DELETE FROM core_user WHERE id = user_id;


admin_add_user - creates new user account

User.objects.create_user(username, email, phone_number, role, password)
INSERT INTO core_user (username, email, phone_number, role, password) 
VALUES ('username', 'email', 'phone', 'role', 'hashed_password');


admin_properties - lists all properties, toggle featured, delete

Property.objects.select_related("seller").all()
SELECT p.*, u.* FROM core_property p 
JOIN core_user u ON p.seller_id = u.id;

Property.objects.get(id=prop_id)
SELECT * FROM core_property WHERE id = prop_id;

prop.is_featured = not prop.is_featured; prop.save()
UPDATE core_property SET is_featured = NOT is_featured WHERE id = prop_id;

prop.delete()
DELETE FROM core_property WHERE id = prop_id;


admin_add_property - creates new property for a seller

Property.objects.create(seller, title, address, city, property_type, price, description)
INSERT INTO core_property (seller_id, title, address, city, property_type, price, description)
VALUES (seller_id, 'title', 'address', 'city', 'type', price, 'description');

PropertyImage.objects.create(property=prop, image=img)
INSERT INTO core_propertyimage (property_id, image) VALUES (prop_id, 'image_path');


admin_payments - approves payments and sends to seller

Payment.objects.get(id=payment_id)
SELECT * FROM core_payment WHERE id = payment_id;

UPDATE core_payment 
SET status = 'APPROVED', platform_cut = x, seller_amount = y,
    approved_by_admin_id = admin_id, approved_at = now
WHERE id = payment_id;

UPDATE core_payment 
SET seller_amount_sent = TRUE, seller_amount_sent_at = now 
WHERE id = payment_id;


================================================================================
TENANT ROUTES - made by tanzeem
================================================================================

tenant_dashboard - shows available properties

Property.objects.select_related("seller").filter(status="AVAILABLE")
SELECT p.*, u.* FROM core_property p 
JOIN core_user u ON p.seller_id = u.id 
WHERE p.status = 'AVAILABLE';


property_detail - shows property with images and booking options

SELECT * FROM core_property WHERE id = property_id;
SELECT * FROM core_propertyimage WHERE property_id = prop_id;


request_visit - tenant submits visit request

INSERT INTO core_visitrequest (property_id, tenant_id, preferred_date, status, created_at)
VALUES (prop_id, user_id, 'date', 'PENDING', now);


================================================================================
SELLER ROUTES - made by saud
================================================================================

seller_dashboard - seller stats

SELECT * FROM core_property WHERE seller_id = seller_id ORDER BY created_at DESC;

SELECT b.*, p.*, t.* FROM core_booking b
JOIN core_property p ON b.property_id = p.id
JOIN core_user t ON b.tenant_id = t.id
WHERE p.seller_id = seller_id ORDER BY b.created_at DESC;


================================================================================
SHARED ROUTES
================================================================================

home - displays featured properties

Property.objects.filter(is_featured=True, status="AVAILABLE")
SELECT * FROM core_property WHERE is_featured = TRUE AND status = 'AVAILABLE';


register - creates new tenant or seller

User.objects.filter(username=username).exists()
SELECT 1 FROM core_user WHERE username = 'username' LIMIT 1;

User.objects.filter(email=email).exists()
SELECT 1 FROM core_user WHERE email = 'email' LIMIT 1;

User.objects.create_user(username, email, first_name, last_name, phone_number, address, role, password)
INSERT INTO core_user (username, email, first_name, last_name, phone_number, address, role, password)
VALUES ('username', 'email', 'first', 'last', 'phone', 'address', 'role', 'hashed_password');
"""
