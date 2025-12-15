from django.db import models
from django.contrib.auth.models import AbstractUser

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
        max_digits=10,
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

    start_date = models.DateField()
    end_date = models.DateField()

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

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    platform_cut = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    seller_amount = models.DecimalField( max_digits=10,
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

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} ({self.status})"



"""
CREATE TABLE user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    username VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,     # hashed password stored by Django auth
    email VARCHAR(254),

    role ENUM('ADMIN', 'SELLER', 'TENANT', 'AGENT') NOT NULL,

    phone_number VARCHAR(15),
    address TEXT,

    is_staff BOOLEAN DEFAULT FALSE,      # required for admin access
    is_superuser BOOLEAN DEFAULT FALSE,  # required for super admin
    last_login DATETIME,
    date_joined DATETIME,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE property (
    id INT PRIMARY KEY AUTO_INCREMENT,

    seller_id INT NOT NULL,              # FK → user(id)

    title VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    city VARCHAR(50) NOT NULL,

    property_type ENUM('SELL', 'RENT') NOT NULL,
    price DECIMAL(10,2) NOT NULL,

    description TEXT,
    image VARCHAR(255),                  # image file path

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (seller_id)
        REFERENCES user(id)
        ON DELETE CASCADE
);


CREATE TABLE visit_request (
    id INT PRIMARY KEY AUTO_INCREMENT,

    property_id INT NOT NULL,             # FK → property(id)
    tenant_id INT NOT NULL,               # FK → user(id)
    agent_id INT,                         # FK → user(id), nullable

    preferred_date DATE NOT NULL,

    status ENUM('PENDING', 'APPROVED', 'REJECTED')
           DEFAULT 'PENDING',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (property_id)
        REFERENCES property(id)
        ON DELETE CASCADE,

    FOREIGN KEY (tenant_id)
        REFERENCES user(id)
        ON DELETE CASCADE,

    FOREIGN KEY (agent_id)
        REFERENCES user(id)
        ON DELETE SET NULL
);

CREATE TABLE booking (
    id INT PRIMARY KEY AUTO_INCREMENT,

    property_id INT NOT NULL,             # FK → property(id)
    tenant_id INT NOT NULL,               # FK → user(id)

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    status ENUM('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED')
           DEFAULT 'PENDING',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (property_id)
        REFERENCES property(id)
        ON DELETE CASCADE,

    FOREIGN KEY (tenant_id)
        REFERENCES user(id)
        ON DELETE CASCADE
);

CREATE TABLE payment (
    id INT PRIMARY KEY AUTO_INCREMENT,

    booking_id INT NOT NULL,              # FK → booking(id)

    amount DECIMAL(10,2) NOT NULL,
    platform_cut DECIMAL(10,2) DEFAULT 0,
    seller_amount DECIMAL(10,2) DEFAULT 0,

    status ENUM('PENDING', 'APPROVED', 'REJECTED')
           DEFAULT 'PENDING',

    approved_by_admin INT,                # FK → user(id)
    approved_at DATETIME,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (booking_id)
        REFERENCES booking(id)
        ON DELETE CASCADE,

    FOREIGN KEY (approved_by_admin)
        REFERENCES user(id)
        ON DELETE SET NULL
);


"""
