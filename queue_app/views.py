# queue_app/views.py

from datetime import timedelta
from functools import wraps

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from rest_framework import viewsets

from .models import Doctor, Patient, Queue, Notification, Department, QueueTicket # 👈 Make sure to import ALL necessary models
from .serializers import DoctorSerializer, PatientSerializer, QueueSerializer, NotificationSerializer, QueueTicketSerializer


def get_doctor_profile(request):
    if not request.user.is_authenticated:
        return None

    try:
        return request.user.doctor_profile
    except ObjectDoesNotExist:
        return None


def doctor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        doctor = get_doctor_profile(request)
        if doctor is None:
            return HttpResponseForbidden("Doctor access only.")

        request.doctor_profile = doctor
        return view_func(request, *args, **kwargs)

    return wrapper


def _priority_label(score):
    if score is None:
        return 'routine'
    if score >= 0.8:
        return 'emergency'
    if score >= 0.5:
        return 'urgent'
    return 'routine'


def _doctor_base_context(doctor):
    queue_items = (
        QueueTicket.objects.filter(doctor=doctor)
        .select_related('patient__user', 'department', 'doctor__user')
        .order_by('check_in_time')
    )
    notifications = Notification.objects.filter(recipient=doctor.user).order_by('-created_at')
    today = timezone.localdate()
    week_ago = timezone.now() - timedelta(days=7)

    current_ticket = queue_items.filter(status='in_consultation').first() or queue_items.filter(status='waiting').first()
    waiting_patients = queue_items.filter(status='waiting')[:10]

    completed_today = queue_items.filter(status='completed', consultation_end_time__date=today).count()
    unread_count = notifications.filter(is_read=False).count()
    total_notifications = notifications.count()

    return {
        'doctor': doctor,
        'doctor_display_name': doctor.user.get_full_name() or doctor.user.username,
        'current_ticket': current_ticket,
        'waiting_patients': waiting_patients,
        'notifications': notifications[:10],
        'patients_seen_today': completed_today,
        'currently_waiting': queue_items.filter(status='waiting').count(),
        'average_time': round(
            sum(ticket.estimated_wait_time or 0 for ticket in waiting_patients) / waiting_patients.count(),
            1,
        ) if waiting_patients else 0,
        'unread_count': unread_count,
        'today_count': notifications.filter(created_at__date=today).count(),
        'week_count': notifications.filter(created_at__gte=week_ago).count(),
        'emergency_count': notifications.filter(message__icontains='emergency').count(),
        'response_rate': int((total_notifications - unread_count) / total_notifications * 100) if total_notifications else 100,
    }

def home(request):
    """
    Retrieves and prepares data for the main queue display.
    """
    # get a patient first
    patient = Patient.objects.first() or None  # Replace with actual logic to get the relevant patient 
    # 1. Fetch all departments
    departments = Department.objects.all()
    
    # 2. Prepare data structure to hold departments and their currently served ticket
    department_data = []
    
    for department in departments:
        # 3. Perform the necessary database query (the logic from your broken template line)
        
        # Find the first ticket for this department that is 'in_consultation'
        # Note: 'queueticket_set' is the reverse relationship name for ForeignKey from QueueTicket to Department.

        in_consultation_ticket = department.queueticket_set.filter(
            status='in_consultation'
        ).first() 

        # Find any other tickets waiting, ordered by entry time/number
        waiting_tickets = department.queueticket_set.filter(
            status='waiting' # Assuming you have a 'waiting' status
        ).order_by('ticket_number')[:5] # Limit to the next 5 waiting tickets

        department_data.append({
            'name': department.name,
            'current_ticket': in_consultation_ticket, # This is the main piece of data you needed!
            'waiting_list': waiting_tickets,
        })
        patient = Patient.objects.first() 
        if not patient:
            patient = Patient.objects.create(
                first_name="Eren",
                last_name="Yeager",
                patient_id="123456"
            )
    # 4. Create the context dictionary
    context = {
        'departments': department_data,
        # You can add other global variables here
        'system_title': "AI Queueing Display",
        'patient' : patient, 
    }
    
    return render(request, 'base.html', context)

def patient_dashboard(request, patient_id):
    patient = Patient.objects.get(pk=patient_id)
    # Logic for patient dashboard view
    return render(request, 'patient/dashboard.html', {'patient': patient})
def patient_register(request):
    # Logic for patient registration view
    return render(request, 'patient/register.html')
def patient_virtual_card(request, patient_id):
    patient = Patient.objects.get(pk=patient_id)
    # Logic for patient virtual card view
    return render(request, 'patient/virtual_card.html', {'patient': patient})


@doctor_required
def doctor_dashboard(request):
    doctor = request.doctor_profile
    context = _doctor_base_context(doctor)
    return render(request, 'doctor/dashboard.html', context)


@doctor_required
def doctor_notifications(request):
    doctor = request.doctor_profile
    context = _doctor_base_context(doctor)
    return render(request, 'doctor/notifications.html', context)


@doctor_required
def doctor_consultation(request, ticket_id):
    doctor = request.doctor_profile
    ticket = get_object_or_404(
        QueueTicket.objects.select_related('patient__user', 'doctor__user', 'department'),
        pk=ticket_id,
        doctor=doctor,
    )

    patient = ticket.patient
    virtual_card_id = ''
    try:
        virtual_card_id = patient.virtual_card.virtual_card_id
    except ObjectDoesNotExist:
        virtual_card_id = ''

    context = {
        'doctor': doctor,
        'doctor_display_name': doctor.user.get_full_name() or doctor.user.username,
        'current_ticket': ticket,
        'patient': patient,
        'patient_age': patient.age if patient.age is not None else 'Not recorded',
        'virtual_card_id': virtual_card_id or 'Not generated',
        'symptom_summary': ticket.symptom_analysis or patient.symptoms or 'No symptom summary available.',
        'priority_label': _priority_label(ticket.ai_priority_score),
    }
    return render(request, 'doctor/consultation.html', context)


@doctor_required
def doctor_patient_detail(request, patient_id):
    doctor = request.doctor_profile
    patient = get_object_or_404(Patient.objects.select_related('user'), pk=patient_id)
    try:
        virtual_card_id = patient.virtual_card.virtual_card_id
    except ObjectDoesNotExist:
        virtual_card_id = 'Not generated'

    latest_ticket = (
        QueueTicket.objects.filter(patient=patient, doctor=doctor)
        .select_related('department')
        .order_by('-check_in_time')
        .first()
    )

    return render(request, 'doctor/patient_detail.html', {
        'doctor': doctor,
        'doctor_display_name': doctor.user.get_full_name() or doctor.user.username,
        'patient': patient,
        'virtual_card_id': virtual_card_id,
        'latest_ticket': latest_ticket,
    })


# Your ViewSets remain unchanged:
class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
  
class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

class QueueViewSet(viewsets.ModelViewSet):
    queryset = Queue.objects.all()
    serializer_class = QueueSerializer
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
class QueueTicketViewSet(viewsets.ModelViewSet):
    queryset = QueueTicket.objects.all()
    serializer_class = QueueTicketSerializer
