# Project370 - Real Estate Management System

A Django-based real estate platform for buying and selling properties.

## Team Members

- **Azmain** - Admin routes and functionality
- **Tanzeem** - Tenant routes and functionality  
- **Saud** - Seller routes and functionality

## Requirements

- Python 3.10+
- Pipenv

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd project370
```

### 2. Install Dependencies

```bash
pipenv install
```

### 3. Activate Virtual Environment

```bash
pipenv shell
```

### 4. Run Database Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ in your browser.

## Project Structure

```
project370/
├── core/                    # Main application
│   ├── models.py           # Database models (User, Property, Booking, etc.)
│   ├── views.py            # All view functions
│   ├── urls.py             # URL routing
│   └── migrations/         # Database migrations
├── templates/              # HTML templates
│   ├── dashboard/          # Dashboard templates for all roles
│   └── registration/       # Login/Register templates
├── media/                  # Uploaded files (property images)
├── project370/             # Project settings
│   ├── settings.py         # Django configuration
│   └── urls.py             # Root URL config
└── manage.py               # Django management script
```

## User Roles

1. **Admin** - Manages users, properties, bookings, payments, and deals
2. **Seller** - Lists properties, views appointments/bookings, receives payments
3. **Tenant** - Browses properties, requests visits, books and purchases properties

## Features

### Admin Features
- Dashboard with system statistics
- User management (add/delete sellers, tenants, agents)
- Property management (add/delete, toggle featured)
- Booking approval/rejection
- Visit request management with agent assignment
- Payment processing and deals tracking

### Seller Features
- Dashboard with property stats and earnings
- Add/edit/delete property listings
- Upload multiple property images
- View appointments and bookings
- Track received and pending payments

### Tenant Features
- Browse available properties
- View property details with images
- Request property visits
- Book properties after visit approval
- Make payments for confirmed bookings
- View purchased properties

## Common Commands

```bash
# Run server
pipenv run python manage.py runserver

# Make migrations after model changes
pipenv run python manage.py makemigrations

# Apply migrations
pipenv run python manage.py migrate

# Run tests
pipenv run python manage.py test

# Create superuser
pipenv run python manage.py createsuperuser
```

## Login URLs

- Admin: http://127.0.0.1:8000/admin-login/
- Tenant/Seller: http://127.0.0.1:8000/login/
- Register: http://127.0.0.1:8000/register/

## Notes

- Property images are stored in `media/property_images/`
- Platform takes 5% cut from each transaction
- Properties are marked as "SOLD" after payment completion
- Featured properties appear on the home page
