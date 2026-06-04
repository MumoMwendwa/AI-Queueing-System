from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator, RegexValidator
import qrcode
from io import BytesIO
from django.core.files import File
import uuid

#
# 1 Doctor Model ; in this model its where we store the details of the doctors in the hospital
#Each doctor can have a specialization, room number, and availability status.
#

class Doctor(models.Model):
    #Link to the User model to associate a doctor with a user account
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100)  # Specialization of the doctor (e.g., Dentist,Cardiologist, Dermatologist)
    room_number = models.CharField(max_length=10, blank=True, null=True)  # the office / room number of the doctors location
    is_available = models.BooleanField(default=True)  # the availability status of the doctor on seeing the patients

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialization}"
    #
    # 2 Patient Model ; in this model its where we store the details of the patients in the hospital who are registered
    # Each patient can have a medical history, contact information, and emergency contact details.
    # It also links to Django's User model so patients can log in.
    
class Patient(models.Model):
    # Link each patient to a user account that he/she can use to login.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    # Patients information 
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)  # Age of the patient
    blood_type = models.CharField(max_length=3, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)  # Contact number of the patient
    emergency_contact = models.CharField(max_length=100, blank=True, null=True)  # Emergency contact details of the patient
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)  # Medical history of the patient if they have ever been treated before and details about the treatement.
    existing_conditions = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)
    # Gender choices for the consistency of data 
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female')],
        default='Male'
    )
    # Optional field to describe symptoms   
    symptoms = models.TextField(blank=True, null=True)
    # Auto-set registration date/time
    registered_at = models.DateTimeField(default=timezone.now) 
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.contact_number}"
    #
    #QUEUE MODEL ; HEART OF THE SYSTEM 
    # in this model its where we store the details of the queue system for patients waiting to see doctors 
    # doctors in a queue can have multiple patients waiting to see them, and each patient can be assigned a position in the queue.
    #  Queue states (status) help track progress:
    #   - waiting: Patient is in queue
    #   - in_progress: Doctor is attending patient
    #   - completed: Appointment finished
    #   - cancelled: Appointment cancelled
    # the Ai Model will use this data to predict wait times and optimize queue management based on historical data .
class Queue(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    # Link patient and doctor together
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='queues')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='queues')
    # Current status entry in the queue 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
# Automatically store creation and update timestamps
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
# AI-predicted waiting time (in minutes)
predicted_wait_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Predicted waiting time in minutes"
    )
def __str__(self):
        return f"Queue Entry: {self.patient.user.get_full_name()} with Dr. {self.doctor.user.get_full_name()} - Status: {self.status}"
#
#NOTIFICATION MODEL ; in this model its where we store the details of the notifications sent to patients regarding their queue status
# Handles messages or alerts sent to users (patients/doctors/admins).
# Notification can be marked as read/unread to help track which notifications have been seen and the ones not seen. 
# #
class Notification(models.Model):
    # who will receive the notification(can be any user)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications') 
    # Notification message text 
    message = models.TextField()
    # Auto record when notification was created
    created_at = models.DateTimeField(auto_now_add=True)
    # Whether the user has seen the notification 
    is_read= models.BooleanField(default=False)
def __str__(self):
        # Show a short preview of the message in admin panel
        return f"To: {self.recipient.username} - {self.message[:30]}..."


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    current_queue_number = models.IntegerField(default=0)

    class Meta:
        db_table = 'departments'
        ordering = ['name']

    def __str__(self):
        return self.name

class VirtualCard(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='virtual_card')
    virtual_card_id = models.CharField(max_length=50, unique=True, db_index=True, blank=True)
    has_physical_card = models.BooleanField(default=False)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)

    # AI fields
    health_risk_score = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'virtual_cards'
        indexes = [
            models.Index(fields=['virtual_card_id']),
        ]

    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.virtual_card_id}"

    def save(self, *args, **kwargs):
        if not self.virtual_card_id:
            self.virtual_card_id = self.generate_virtual_card_id()
        if not self.qr_code:
            self.generate_qr_code()
        super().save(*args, **kwargs)

    def generate_virtual_card_id(self):
        return f"VC-{uuid.uuid4().hex[:12].upper()}"

    def generate_qr_code(self):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr_data = f"{self.virtual_card_id}|{self.patient.user.get_full_name()}|{self.patient.contact_number or ''}"
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, 'PNG')
        buffer.seek(0)

        self.qr_code.save(f'qr_{self.virtual_card_id}.png', File(buffer), save=False)

class QueueTicket(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('in_consultation', 'In Consultation'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    ticket_number = models.CharField(max_length=20, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, db_index=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, db_index=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    check_in_time = models.DateTimeField(auto_now_add=True)
    consultation_start_time = models.DateTimeField(null=True, blank=True)
    consultation_end_time = models.DateTimeField(null=True, blank=True)
    estimated_wait_time = models.IntegerField(null=True, blank=True)  # minutes

    # AI-enhanced fields
    ai_priority_score = models.FloatField(default=0.5)  # 0-1
    predicted_consultation_time = models.IntegerField(null=True, blank=True)  # minutes
    ai_suggested_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_suggestions')
    symptom_analysis = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'queue_tickets'
        indexes = [
            models.Index(fields=['status', 'department']),
            models.Index(fields=['check_in_time']),
            models.Index(fields=['patient', 'status']),
        ]
        ordering = ['check_in_time']

    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.patient.user.get_full_name()}"

class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, db_index=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, db_index=True)
    visit_date = models.DateTimeField(auto_now_add=True)
    symptoms = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    medications_prescribed = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    next_visit_date = models.DateField(null=True, blank=True)

    # AI analysis fields
    ai_diagnosis_confidence = models.FloatField(null=True, blank=True)
    treatment_effectiveness = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'medical_records'
        indexes = [
            models.Index(fields=['patient', 'visit_date']),
            models.Index(fields=['visit_date']),
        ]
        ordering = ['-visit_date']

    def __str__(self):
        return f"Record {self.id} - {self.patient.user.get_full_name()} - {self.visit_date}"

