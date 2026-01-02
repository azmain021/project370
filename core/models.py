from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver

class User(AbstractUser):
    ROLE_CHOICES = (
    ("ADMIN", "Admin"),
    ("SELLER", "Seller"),
    ("TENANT", "Tenant"),
    ("AGENT", "Agent"),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class Property(models.Model):

    STATUS_CHOICES = (
        ("AVAILABLE", "Available"),
        ("BOOKED", "Booked"),
        ("SOLD", "Sold"),
        ("INACTIVE", "Inactive"),
    )

    PROPERTY_TYPES = (
        ("SELL", "For Sale"),
        ("RENT", "For Rent"),
    )

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="properties",
        limit_choices_to={"role": "SELLER"},
    )

    title = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=50)

    property_type = models.CharField(
        max_length=10,
        choices=PROPERTY_TYPES
    )

    price = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="AVAILABLE"
    )

    description = models.TextField(blank=True)

    image = models.ImageField(
        upload_to="property_images/",
        blank=True,
        null=True
    )

    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.status})"



class VisitRequest(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='visit_requests'
    )

    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='visit_requests',
        limit_choices_to={'role': 'TENANT'},
    )

    # agent assigned only after approval (still not working)
    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_visits',
        limit_choices_to={'role': 'AGENT'},
    )

    preferred_date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Visit: {self.property.title} → {self.tenant.username}"



class Booking(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        limit_choices_to={'role': 'TENANT'},
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.property.title} → {self.tenant.username} ({self.status})"



class Payment(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    amount = models.DecimalField(max_digits=15, decimal_places=2)

    platform_cut = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    seller_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    approved_by_admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_payments',
        limit_choices_to={'role': 'ADMIN'},
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    seller_amount_sent = models.BooleanField(default=False)

    seller_amount_sent_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} ({self.status})"


# ============================================================================
# SIGNALS - Auto-update property status when bookings are deleted
# ============================================================================

@receiver(pre_delete, sender=Booking)
def reset_property_on_booking_delete(sender, instance, **kwargs):
    """
    When a booking is deleted (e.g., user deletion), check if property 
    should be set back to AVAILABLE.
    """
    # Only reset if this was a CONFIRMED or PENDING booking
    if instance.status in ['CONFIRMED', 'PENDING']:
        # Check if there are other active bookings for this property
        other_bookings = Booking.objects.filter(
            property=instance.property,
            status__in=['CONFIRMED', 'PENDING']
        ).exclude(id=instance.id).exists()
        
        # If no other active bookings, set property back to available
        if not other_bookings:
            instance.property.status = 'AVAILABLE'
            instance.property.save()


# ============================================================================
# SQL COMMANDS FOR ALL MODELS
# ============================================================================

# ----------------------------------------------------------------------------
# USER TABLE (extends Django's AbstractUser)
# ----------------------------------------------------------------------------
# CREATE TABLE core_user (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     password VARCHAR(128) NOT NULL,
#     last_login DATETIME,
#     is_superuser BOOLEAN NOT NULL DEFAULT 0,
#     username VARCHAR(150) NOT NULL UNIQUE,
#     first_name VARCHAR(150) NOT NULL,
#     last_name VARCHAR(150) NOT NULL,
#     email VARCHAR(254) NOT NULL,
#     is_staff BOOLEAN NOT NULL DEFAULT 0,
#     is_active BOOLEAN NOT NULL DEFAULT 1,
#     date_joined DATETIME NOT NULL,
#     role VARCHAR(10) NOT NULL CHECK (role IN ('ADMIN', 'SELLER', 'TENANT', 'AGENT')),
#     phone_number VARCHAR(15),
#     address TEXT
# );

# ----------------------------------------------------------------------------
# PROPERTY TABLE
# ----------------------------------------------------------------------------
# CREATE TABLE core_property (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     seller_id INTEGER NOT NULL,
#     title VARCHAR(100) NOT NULL,
#     address TEXT NOT NULL,
#     city VARCHAR(50) NOT NULL,
#     property_type VARCHAR(10) NOT NULL CHECK (property_type IN ('SELL', 'RENT')),
#     price DECIMAL(10, 2) NOT NULL,
#     status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE', 'BOOKED', 'INACTIVE')),
#     description TEXT,
#     image VARCHAR(100),
#     is_featured BOOLEAN NOT NULL DEFAULT 0,
#     created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (seller_id) REFERENCES core_user(id) ON DELETE CASCADE
# );

# ----------------------------------------------------------------------------
# VISIT REQUEST TABLE
# ----------------------------------------------------------------------------
# CREATE TABLE core_visitrequest (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     property_id INTEGER NOT NULL,
#     tenant_id INTEGER NOT NULL,
#     agent_id INTEGER,
#     preferred_date DATE NOT NULL,
#     status VARCHAR(10) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
#     created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (property_id) REFERENCES core_property(id) ON DELETE CASCADE,
#     FOREIGN KEY (tenant_id) REFERENCES core_user(id) ON DELETE CASCADE,
#     FOREIGN KEY (agent_id) REFERENCES core_user(id) ON DELETE SET NULL
# );

# ----------------------------------------------------------------------------
# BOOKING TABLE
# ----------------------------------------------------------------------------
# CREATE TABLE core_booking (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     property_id INTEGER NOT NULL,
#     tenant_id INTEGER NOT NULL,
#     status VARCHAR(10) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED')),
#     created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (property_id) REFERENCES core_property(id) ON DELETE CASCADE,
#     FOREIGN KEY (tenant_id) REFERENCES core_user(id) ON DELETE CASCADE
# );

# ----------------------------------------------------------------------------
# PAYMENT TABLE
# ----------------------------------------------------------------------------
# CREATE TABLE core_payment (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     booking_id INTEGER NOT NULL,
#     amount DECIMAL(10, 2) NOT NULL,
#     platform_cut DECIMAL(10, 2) NOT NULL DEFAULT 0,
#     seller_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
#     status VARCHAR(10) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
#     approved_by_admin_id INTEGER,
#     approved_at DATETIME,
#     created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (booking_id) REFERENCES core_booking(id) ON DELETE CASCADE,
#     FOREIGN KEY (approved_by_admin_id) REFERENCES core_user(id) ON DELETE SET NULL
# );
