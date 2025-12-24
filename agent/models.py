from django.db import models
import uuid

class Property(models.Model):
    name = models.CharField(max_length=255)
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.IntegerField(null=True, blank=True)
    completion_status = models.CharField(max_length=100, null=True, blank=True) # off plan/available
    unit_type = models.CharField(max_length=100, null=True, blank=True) # apartment/villa
    developer_name = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    area_sq_mtrs = models.FloatField(null=True, blank=True)
    property_type = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    completion_date = models.CharField(max_length=100, null=True, blank=True) # Keeping as string as format might vary
    features = models.TextField(null=True, blank=True) # JSON or list string
    facilities = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.unit_type} ({self.city})"

class VisitBooking(models.Model):
    lead_name = models.CharField(max_length=255)
    lead_email = models.EmailField()
    project_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100, null=True, blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'visit_bookings'

    def __str__(self):
        return f"Booking: {self.lead_name} for {self.project_name}"

class Lead(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    preferences = models.TextField(null=True, blank=True) # JSON or text summary
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lead: {self.first_name} {self.last_name}"

class Message(models.Model):
    conversation_id = models.CharField(max_length=255)
    role = models.CharField(max_length=50) # 'user' or 'assistant'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.conversation_id} - {self.role}: {self.content[:50]}"
