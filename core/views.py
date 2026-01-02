from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum

from .models import User, Property, Booking, Payment, VisitRequest, PropertyImage


#  displays featured properties
def home(request):
    # Get all featured properties (no limit - admin can feature as many as they want)
    featured_properties = list(Property.objects.filter(is_featured=True, status="AVAILABLE"))
    
    return render(request, "home.html", {"featured_properties": featured_properties})


# auth routes -all users

# login  based on role
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


# logout 
def logout_view(request):
    logout(request)
    return redirect("login")


# register  new tenant or seller account
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

        # Auto login 
        login(request, user)
        return redirect("role-redirect")

    return render(request, "registration/register.html")


# role_redirect 
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


# admin routes -  azmain

# admin_dashboard 
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


#  lists  users,deletion
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


#  creates new user 
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


# a lists  properties,feature prop, delete
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


#creates new property for a seller
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

        # Handle mimages
        images = request.FILES.getlist("images")
        for img in images:
            PropertyImage.objects.create(property=prop, image=img)

        return redirect("admin-properties")

    context = {
        "sellers": sellers,
    }
    return render(request, "dashboard/admin_add_property.html", context)


# approves payments and sends to seller
@login_required
def admin_payments(request):
    if request.user.role != "ADMIN":
        return redirect("home")

    # I "Send to Seller" button
    if request.method == "POST":
        action = request.POST.get("action")
        payment_id = request.POST.get("payment_id")
        
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            payment = None

        if payment:
            if action == "approve":
              
                if payment.status == "PENDING":
                    
                    # Platform fee is 10%
                    payment.platform_cut = payment.amount * Decimal('0.10')
                    payment.seller_amount = payment.amount - payment.platform_cut

                    payment.status = "APPROVED"
                    payment.approved_by_admin = request.user
                    payment.approved_at = timezone.now()
                    
                    
                    if payment.booking.property.property_type == "SELL":
                        payment.booking.property.status = "BOOKED"
                        payment.booking.property.save()
                    
                    payment.save()
            
            elif action == "send_to_seller":
                # Only send if approved 
                if payment.status == "APPROVED" and not payment.seller_amount_sent:
                    payment.seller_amount_sent = True
                    payment.seller_amount_sent_at = timezone.now()
                    payment.save()

        return redirect("admin-payments")

    # pending and recently approved payments
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

    # Calculate fee
    total_platform_cut = sum(p.platform_cut for p in approved_payments)

    context = {
        "pending_payments": pending_payments,
        "approved_payments": approved_payments,
        "total_platform_cut": total_platform_cut,
    }

    return render(request, "dashboard/admin_payments.html", context)


#shows completed transactions
def admin_deals(request):
    if request.user.role != "ADMIN":
        return redirect("home")

    
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


# tenant routes - tanzeem

#  shows property with all images and booking options
@login_required
def property_detail(request, property_id):
    if request.user.role != "TENANT":
        return redirect("home")

    prop = get_object_or_404(Property, id=property_id)
    images = prop.images.all()

    
    has_pending_visit = VisitRequest.objects.filter(
        property=prop,
        tenant=request.user,
        status="PENDING"
    ).exists()

   
    has_approved_visit = VisitRequest.objects.filter(
        property=prop,
        tenant=request.user,
        status="APPROVED"
    ).exists()

    
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


#  available properties for tenant
@login_required
def tenant_dashboard(request):
    if request.user.role != "TENANT":
        return redirect("home")

    
    properties = Property.objects.select_related("seller").filter(status="AVAILABLE")

   
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


# visit request for property
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

        #  tenant  pending request
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


#  shows tenant's visit requests
@login_required
def tenant_my_visits(request):
    if request.user.role != "TENANT":
        return redirect("home")

    # property IDs where tenant has completed payment 
    completed_property_ids = set(
        Booking.objects.filter(
            tenant=request.user,
            status="COMPLETED"
        ).values_list("property_id", flat=True)
    )

    
    visits = VisitRequest.objects.filter(tenant=request.user).exclude(
        property_id__in=completed_property_ids
    ).select_related(
        "property", "agent"
    ).order_by("-created_at")

    
    booked_property_ids = set(
        Booking.objects.filter(
            tenant=request.user,
            status__in=["PENDING", "CONFIRMED"]
        ).values_list("property_id", flat=True)
    )

    
    confirmed_property_ids = set(
        Booking.objects.filter(status="CONFIRMED").values_list("property_id", flat=True)
    )

    # Add a flag 
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


# admin approves/rejects visit requests, assigns agents - Azmain
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


# tenant books property after visit approved
@login_required
def book_property(request, property_id):
    if request.user.role != "TENANT":
        return redirect("home")

    if request.method == "POST":
        try:
            prop = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            return redirect("tenant-my-visits")

        # Check if tenant already has an active booking 
        existing = Booking.objects.filter(
            property=prop,
            tenant=request.user,
            status__in=["PENDING", "CONFIRMED"]
        ).exists()

        #  check if property is already booked by someone else
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


# tenant's pending and confirmed bookings
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


# ttenant's purchased properties
@login_required
def tenant_my_properties(request):
    if request.user.role != "TENANT":
        return redirect("home")

    
    completed_bookings = Booking.objects.filter(
        tenant=request.user,
        status="COMPLETED"
    ).select_related("property", "property__seller").prefetch_related("payments")

   
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


# admin confirms or cancels booking requests
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


# tenant pays for confirmed booking, marks property as sold
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
        
        
        Payment.objects.create(
            booking=booking,
            amount=amount,
            platform_cut=platform_cut,
            seller_amount=seller_amount,
            status="APPROVED",
            approved_at=timezone.now()
        )
        
        # Mark booking as COMPLETED 
        booking.status = "COMPLETED"
        booking.save()
        
        # Mark property as SOLD and remove from featured
        booking.property.status = "SOLD"
        booking.property.is_featured = False
        booking.property.save()

    return redirect("payment-confirmation", booking_id=booking_id)


# shows payment success page
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

# shows seller stats, properties, bookings, payments
@login_required
def seller_dashboard(request):
    if request.user.role != "SELLER":
        return redirect("home")

    seller = request.user
    properties = Property.objects.filter(seller=seller).order_by("-created_at")
    
   
    bookings = Booking.objects.filter(property__seller=seller).select_related(
        "property", "tenant"
    ).order_by("-created_at")
    
   
    appointments = VisitRequest.objects.filter(property__seller=seller).select_related(
        "property", "tenant"
    ).order_by("-created_at")
    
    
    payments_sent = Payment.objects.filter(
        booking__property__seller=seller,
        status="APPROVED",
        seller_amount_sent=True
    )
    payments_total = payments_sent.aggregate(Sum("seller_amount"))["seller_amount__sum"] or 0
    
    
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


#  seller's properties
@login_required
def seller_properties(request):
    if request.user.role != "SELLER":
        return redirect("home")

    properties = Property.objects.filter(seller=request.user).order_by("-created_at")

    context = {"properties": properties}
    return render(request, "dashboard/seller_properties.html", context)


# creates new property listing
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

        prop = Property.objects.create(
            title=title,
            description=description,
            address=address,
            city=city,
            price=price,
            property_type=property_type,
            seller=request.user,
        )

        images = request.FILES.getlist("images")
        for img in images:
            PropertyImage.objects.create(property=prop, image=img)

        return redirect("seller_properties")

    return render(request, "dashboard/seller_add_property.html")


# updates property details and images
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


# dedlete property listing
@login_required
def delete_property(request, property_id):
    prop = get_object_or_404(Property, id=property_id, seller=request.user)
    if request.method == "POST":
        prop.delete()
    return redirect("seller_properties")


#  visit requests for seller's properties
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


#  bookings for seller's properties
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


# shows received and pending payments for seller
@login_required
def seller_payments(request):
    if request.user.role != "SELLER":
        return redirect("home")

   
    payments = Payment.objects.filter(
        booking__property__seller=request.user,
        status="APPROVED",
        seller_amount_sent=True
    ).select_related(
        "booking", "booking__property", "booking__tenant"
    ).order_by("-seller_amount_sent_at")
    
   
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
SQL Queries Reference

Raw SQL equivalents of the Django ORM calls used in each view function.


SHARED ROUTES

home()
SELECT * FROM core_property WHERE is_featured = 1 AND status = 'AVAILABLE';

register_view()
SELECT 1 FROM core_user WHERE username = ? LIMIT 1;
SELECT 1 FROM core_user WHERE email = ? LIMIT 1;
INSERT INTO core_user (username, email, first_name, last_name, phone_number, address, role, password) VALUES (?, ?, ?, ?, ?, ?, ?, ?);


ADMIN ROUTES (azmain)

admin_dashboard()
SELECT COUNT(*) FROM core_user;
SELECT COUNT(*) FROM core_user WHERE role = 'SELLER';
SELECT COUNT(*) FROM core_user WHERE role = 'TENANT';
SELECT COUNT(*) FROM core_property;
SELECT COUNT(*) FROM core_booking;
SELECT COUNT(*) FROM core_payment;
SELECT COUNT(*) FROM core_payment WHERE seller_amount_sent = 1;
SELECT COUNT(*) FROM core_payment WHERE status = 'PENDING';
SELECT COUNT(*) FROM core_visitrequest WHERE status = 'PENDING';
SELECT COUNT(*) FROM core_booking WHERE status = 'PENDING';

admin_users()
SELECT * FROM core_user WHERE role = 'SELLER';
SELECT * FROM core_user WHERE role = 'TENANT';
SELECT * FROM core_user WHERE role = 'AGENT';
DELETE FROM core_user WHERE id = ?;

admin_add_user()
INSERT INTO core_user (username, email, phone_number, role, password) VALUES (?, ?, ?, ?, ?);

admin_properties()
SELECT p.*, u.* FROM core_property p JOIN core_user u ON p.seller_id = u.id;
UPDATE core_property SET is_featured = NOT is_featured WHERE id = ?;
DELETE FROM core_property WHERE id = ?;

admin_add_property()
INSERT INTO core_property (seller_id, title, address, city, property_type, price, description) VALUES (?, ?, ?, ?, ?, ?, ?);
INSERT INTO core_propertyimage (property_id, image) VALUES (?, ?);

admin_payments()
SELECT * FROM core_payment WHERE id = ?;
UPDATE core_payment SET status = 'APPROVED', platform_cut = ?, seller_amount = ?, approved_by_admin_id = ?, approved_at = ? WHERE id = ?;
UPDATE core_payment SET seller_amount_sent = 1, seller_amount_sent_at = ? WHERE id = ?;

admin_deals()
SELECT p.*, b.*, prop.*, s.*, t.* FROM core_payment p
JOIN core_booking b ON p.booking_id = b.id
JOIN core_property prop ON b.property_id = prop.id
JOIN core_user s ON prop.seller_id = s.id
JOIN core_user t ON b.tenant_id = t.id
WHERE p.seller_amount_sent = 1 ORDER BY p.seller_amount_sent_at DESC;

admin_visit_requests()
SELECT v.*, p.*, t.* FROM core_visitrequest v
JOIN core_property p ON v.property_id = p.id
JOIN core_user t ON v.tenant_id = t.id
WHERE v.status = 'PENDING' ORDER BY v.created_at DESC;

SELECT v.*, p.*, t.*, a.* FROM core_visitrequest v
JOIN core_property p ON v.property_id = p.id
JOIN core_user t ON v.tenant_id = t.id
LEFT JOIN core_user a ON v.agent_id = a.id
WHERE v.status = 'APPROVED' ORDER BY v.created_at DESC LIMIT 10;

UPDATE core_visitrequest SET status = 'APPROVED', agent_id = ? WHERE id = ?;
UPDATE core_visitrequest SET status = 'REJECTED' WHERE id = ?;

admin_bookings()
SELECT b.*, p.*, t.* FROM core_booking b
JOIN core_property p ON b.property_id = p.id
JOIN core_user t ON b.tenant_id = t.id
WHERE b.status = 'PENDING' ORDER BY b.created_at DESC;

UPDATE core_booking SET status = 'CONFIRMED' WHERE id = ?;
UPDATE core_property SET status = 'BOOKED' WHERE id = ?;
UPDATE core_booking SET status = 'CANCELLED' WHERE id = ?;


TENANT ROUTES (tanzeem)

tenant_dashboard()
SELECT p.*, u.* FROM core_property p
JOIN core_user u ON p.seller_id = u.id
WHERE p.status = 'AVAILABLE';

SELECT COUNT(DISTINCT b.id) FROM core_booking b
JOIN core_payment pay ON pay.booking_id = b.id
WHERE b.tenant_id = ? AND b.status = 'COMPLETED' AND pay.status = 'APPROVED';

property_detail()
SELECT * FROM core_property WHERE id = ?;
SELECT * FROM core_propertyimage WHERE property_id = ?;
SELECT 1 FROM core_visitrequest WHERE property_id = ? AND tenant_id = ? AND status = 'PENDING' LIMIT 1;
SELECT 1 FROM core_visitrequest WHERE property_id = ? AND tenant_id = ? AND status = 'APPROVED' LIMIT 1;
SELECT 1 FROM core_booking WHERE property_id = ? AND tenant_id = ? AND status IN ('PENDING', 'CONFIRMED', 'COMPLETED') LIMIT 1;

request_visit()
SELECT 1 FROM core_visitrequest WHERE property_id = ? AND tenant_id = ? AND status = 'PENDING' LIMIT 1;
INSERT INTO core_visitrequest (property_id, tenant_id, preferred_date, status, created_at) VALUES (?, ?, ?, 'PENDING', ?);

tenant_my_visits()
SELECT property_id FROM core_booking WHERE tenant_id = ? AND status = 'COMPLETED';
SELECT v.*, p.*, a.* FROM core_visitrequest v
JOIN core_property p ON v.property_id = p.id
LEFT JOIN core_user a ON v.agent_id = a.id
WHERE v.tenant_id = ? AND v.property_id NOT IN (?) ORDER BY v.created_at DESC;
SELECT property_id FROM core_booking WHERE tenant_id = ? AND status IN ('PENDING', 'CONFIRMED');
SELECT property_id FROM core_booking WHERE status = 'CONFIRMED';

book_property()
SELECT 1 FROM core_booking WHERE property_id = ? AND tenant_id = ? AND status IN ('PENDING', 'CONFIRMED') LIMIT 1;
SELECT 1 FROM core_booking WHERE property_id = ? AND status = 'CONFIRMED' LIMIT 1;
INSERT INTO core_booking (property_id, tenant_id, status, created_at) VALUES (?, ?, 'PENDING', ?);

tenant_my_bookings()
SELECT b.*, p.*, s.* FROM core_booking b
JOIN core_property p ON b.property_id = p.id
JOIN core_user s ON p.seller_id = s.id
WHERE b.tenant_id = ? AND b.status != 'COMPLETED' ORDER BY b.created_at DESC;

tenant_my_properties()
SELECT b.*, p.*, s.*, pay.* FROM core_booking b
JOIN core_property p ON b.property_id = p.id
JOIN core_user s ON p.seller_id = s.id
JOIN core_payment pay ON pay.booking_id = b.id
WHERE b.tenant_id = ? AND b.status = 'COMPLETED' AND pay.status = 'APPROVED';

initiate_payment()
SELECT * FROM core_booking WHERE id = ? AND tenant_id = ? AND status = 'CONFIRMED';
SELECT 1 FROM core_payment WHERE booking_id = ? LIMIT 1;
INSERT INTO core_payment (booking_id, amount, platform_cut, seller_amount, status, approved_at) VALUES (?, ?, ?, ?, 'APPROVED', ?);
UPDATE core_booking SET status = 'COMPLETED' WHERE id = ?;
UPDATE core_property SET status = 'SOLD', is_featured = 0 WHERE id = ?;

payment_confirmation()
SELECT * FROM core_booking WHERE id = ? AND tenant_id = ?;
SELECT * FROM core_payment WHERE booking_id = ?;


SELLER ROUTES (saud)

seller_dashboard()
SELECT * FROM core_property WHERE seller_id = ? ORDER BY created_at DESC;

SELECT b.*, p.*, t.* FROM core_booking b
JOIN core_property p ON b.property_id = p.id
JOIN core_user t ON b.tenant_id = t.id
WHERE p.seller_id = ? ORDER BY b.created_at DESC;

SELECT v.*, p.*, t.* FROM core_visitrequest v
JOIN core_property p ON v.property_id = p.id
JOIN core_user t ON v.tenant_id = t.id
WHERE p.seller_id = ? ORDER BY v.created_at DESC;

SELECT SUM(seller_amount) FROM core_payment pay
JOIN core_booking b ON pay.booking_id = b.id
JOIN core_property p ON b.property_id = p.id
WHERE p.seller_id = ? AND pay.status = 'APPROVED' AND pay.seller_amount_sent = 1;

SELECT SUM(seller_amount) FROM core_payment pay
JOIN core_booking b ON pay.booking_id = b.id
JOIN core_property p ON b.property_id = p.id
WHERE p.seller_id = ? AND pay.status = 'APPROVED' AND pay.seller_amount_sent = 0;

seller_properties()
SELECT * FROM core_property WHERE seller_id = ? ORDER BY created_at DESC;

add_property()
INSERT INTO core_property (title, description, address, city, price, property_type, seller_id) VALUES (?, ?, ?, ?, ?, ?, ?);
INSERT INTO core_propertyimage (property_id, image) VALUES (?, ?);

edit_property()
SELECT * FROM core_property WHERE id = ? AND seller_id = ?;
UPDATE core_property SET title = ?, description = ?, address = ?, city = ?, price = ?, property_type = ? WHERE id = ?;
INSERT INTO core_propertyimage (property_id, image) VALUES (?, ?);
DELETE FROM core_propertyimage WHERE id IN (?) AND property_id = ?;

delete_property()
SELECT * FROM core_property WHERE id = ? AND seller_id = ?;
DELETE FROM core_property WHERE id = ?;

seller_appointments()
SELECT * FROM core_property WHERE seller_id = ?;
SELECT v.*, p.*, t.*, a.* FROM core_visitrequest v
JOIN core_property p ON v.property_id = p.id
JOIN core_user t ON v.tenant_id = t.id
LEFT JOIN core_user a ON v.agent_id = a.id
WHERE p.seller_id = ? ORDER BY v.created_at DESC;

seller_bookings()
SELECT * FROM core_property WHERE seller_id = ?;
SELECT b.*, p.*, t.* FROM core_booking b
JOIN core_property p ON b.property_id = p.id
JOIN core_user t ON b.tenant_id = t.id
WHERE p.seller_id = ? ORDER BY b.created_at DESC;

seller_payments()
SELECT pay.*, b.*, p.*, t.* FROM core_payment pay
JOIN core_booking b ON pay.booking_id = b.id
JOIN core_property p ON b.property_id = p.id
JOIN core_user t ON b.tenant_id = t.id
WHERE p.seller_id = ? AND pay.status = 'APPROVED' AND pay.seller_amount_sent = 1
ORDER BY pay.seller_amount_sent_at DESC;

SELECT pay.*, b.*, p.*, t.* FROM core_payment pay
JOIN core_booking b ON pay.booking_id = b.id
JOIN core_property p ON b.property_id = p.id
JOIN core_user t ON b.tenant_id = t.id
WHERE p.seller_id = ? AND pay.status = 'APPROVED' AND pay.seller_amount_sent = 0
ORDER BY pay.approved_at DESC;
"""
