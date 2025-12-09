from django.contrib import admin

# Register your models here.
from .models import User, Property, VisitRequest, Booking, Payment

admin.site.register(User)
admin.site.register(Property)
admin.site.register(VisitRequest)
admin.site.register(Booking)
admin.site.register(Payment)
