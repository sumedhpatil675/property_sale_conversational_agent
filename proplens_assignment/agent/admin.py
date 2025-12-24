from django.contrib import admin
from .models import Property, Booking, Lead, Message

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'price', 'unit_type', 'completion_status')
    search_fields = ('name', 'city', 'developer_name')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('lead_name', 'lead_email', 'project_name', 'city', 'booking_date')

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'created_at')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation_id', 'role', 'content', 'created_at')
    list_filter = ('conversation_id', 'role')
