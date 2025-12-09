from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('SELLER', 'Seller'),
        ('TENANT', 'Tenant'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='TENANT')
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Property(models.Model):
    PROPERTY_TYPES = (
        ('FLAT', 'Flat'),
        ('HOUSE', 'House'),
        ('ROOM', 'Room'),
    )

    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('NOT_AVAILABLE', 'Not Available'),
    )

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='properties',
        limit_choices_to={'role': 'SELLER'},
    )
    title = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=50)
    property_type = models.CharField(max_length=10, choices=PROPERTY_TYPES)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.city}"


class VisitRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='visit_requests')
    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='visit_requests',
        limit_choices_to={'role': 'TENANT'},
    )
    preferred_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Visit for {self.property.title} by {self.tenant.username}"


class Booking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    )

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        limit_choices_to={'role': 'TENANT'},
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.property.title} - {self.tenant.username} ({self.status})"


class Payment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_cut = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    seller_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by_admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_payments',
        limit_choices_to={'role': 'ADMIN'},
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.id} for booking {self.booking.id} ({self.status})"
