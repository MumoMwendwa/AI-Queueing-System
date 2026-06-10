# queue_app/views.py

from datetime import timedelta
from functools import wraps
from datetime import datetime
from types import SimpleNamespace

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from rest_framework import viewsets

from .models import Doctor, Patient, Queue, Notification, Department, QueueTicket # 👈 Make sure to import ALL necessary models
from .serializers import DoctorSerializer, PatientSerializer, QueueSerializer, NotificationSerializer, QueueTicketSerializer
from utils.helpers import calculate_age, generate_random_string
from django.db import IntegrityError


def get_doctor_profile(request):
    if not request.user.is_authenticated:
        return None

    try:
        return request.user.doctor_profile
    except ObjectDoesNotExist:
        return None


def get_patient_profile(request):
    if not request.user.is_authenticated:
        return None
    try:
        return request.user.patient_profile
    except ObjectDoesNotExist:
        return None


def doctor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")

        doctor = get_doctor_profile(request)
        if doctor is None:
            return HttpResponseForbidden("Doctor access only.")

        request.doctor_profile = doctor
        return view_func(request, *args, **kwargs)

    return wrapper


def _post_login_redirect(user):
    """Send a freshly logged-in user to the page that fits their role."""
    try:
        user.doctor_profile
        return redirect('doctor_dashboard')
    except ObjectDoesNotExist:
        pass

    try:
        patient = user.patient_profile
        return redirect('patient_dashboard', patient_id=patient.pk)
    except ObjectDoesNotExist:
        pass

    if user.is_staff:
        return redirect('/admin/')
    return redirect('home')


def login_view(request):
    """Unified login page for doctors and patients."""
    if request.user.is_authenticated:
        return _post_login_redirect(request.user)

    next_url = request.POST.get('next') or request.GET.get('next', '')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if next_url:
                return redirect(next_url)
            return _post_login_redirect(user)
        messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'registration/login.html', {'next': next_url})


def logout_view(request):
    logout(request)
    return redirect('login')


def doctor_register(request):
    """Self-service registration for doctors (creates a User + Doctor profile)."""
    if request.user.is_authenticated:
        return _post_login_redirect(request.user)

    form_data = {}
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        specialization = request.POST.get('specialization', '').strip()
        room_number = request.POST.get('room_number', '').strip()

        form_data = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'specialization': specialization,
            'room_number': room_number,
        }

        errors = []
        if not username:
            errors.append('Username is required.')
        if not password:
            errors.append('Password is required.')
        if password and password != confirm_password:
            errors.append('Passwords do not match.')
        if not specialization:
            errors.append('Specialization is required.')
        if username and User.objects.filter(username=username).exists():
            errors.append('That username is already taken.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
            )
            Doctor.objects.create(
                user=user,
                specialization=specialization,
                room_number=room_number or None,
            )
            login(request, user)
            messages.success(request, 'Doctor account created successfully.')
            return redirect('doctor_dashboard')

    return render(request, 'doctor/register.html', {'form_data': form_data})


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
    # Home is a public landing page; do not force-select or create a patient record.
    patient = None
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
    # 4. Create the context dictionary
    context = {
        'departments': department_data,
        # You can add other global variables here
        'system_title': "AI Queueing Display",
        'patient' : patient, 
    }
    
    return render(request, 'base.html', context)

def patient_dashboard(request, patient_id):
    patient = get_object_or_404(Patient.objects.select_related('user'), pk=patient_id)

    # Attach convenient attributes expected by templates
    patient.first_name = getattr(patient.user, 'first_name', '')
    patient.last_name = getattr(patient.user, 'last_name', '')
    patient.email = getattr(patient.user, 'email', '')

    # Virtual card info
    try:
        vc = patient.virtual_card
        patient.virtual_card_id = getattr(vc, 'virtual_card_id', '')
        patient.qr_code = getattr(vc, 'qr_code', None)
    except ObjectDoesNotExist:
        patient.virtual_card_id = ''
        patient.qr_code = None

    # Find current ticket for this patient (waiting or in_consultation)
    current_ticket = (
        QueueTicket.objects.filter(patient=patient, status__in=['waiting', 'in_consultation'])
        .select_related('department', 'doctor')
        .order_by('-check_in_time')
        .first()
    )

    # Provide a safe fallback so template doesn't error
    if not current_ticket:
        current_ticket = SimpleNamespace(
            department=SimpleNamespace(name='Not in queue'),
            doctor=None,
            ticket_number='N/A',
            estimated_wait_time=0,
        )

    return render(request, 'patient/dashboard.html', {
        'patient': patient,
        'current_ticket': current_ticket,
    })
def patient_register(request):
    # Handle POST registration
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '').strip()
        blood_type = request.POST.get('blood_type', '').strip()
        allergies = request.POST.get('allergies', '').strip()
        address = request.POST.get('address', '').strip()
        emergency_contact = request.POST.get('emergency_contact', '').strip()
        relationship = request.POST.get('relationship', '').strip()
        existing_conditions = request.POST.get('existing_conditions', '').strip()
        current_medications = request.POST.get('current_medications', '').strip()
        symptoms = request.POST.get('symptoms', '').strip()
        password = request.POST.get('password', '')

        medical_history_parts = [
            f"Symptoms: {symptoms}" if symptoms else "",
            f"Existing Conditions: {existing_conditions}" if existing_conditions else "",
            f"Current Medications: {current_medications}" if current_medications else "",
        ]
        medical_history = "\n".join(part for part in medical_history_parts if part)

        # Determine username
        username = email or phone or f'user_{User.objects.count() + 1}'

        try:
            user, created = User.objects.get_or_create(username=username, defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
            })
        except IntegrityError:
            # Race or unique constraint issue — try to load existing user, otherwise create with a safe unique username
            try:
                user = User.objects.get(username=username)
                created = False
            except User.DoesNotExist:
                safe_username = f"{username}_{generate_random_string(6)}"
                user = User.objects.create(username=safe_username, first_name=first_name, last_name=last_name, email=email)
                user.set_unusable_password()
                user.save()
                created = True

        user.first_name = first_name
        user.last_name = last_name
        if email:
            user.email = email
        user.save()

        # Set a usable password when supplied so patients can log in later;
        # otherwise keep the account password-less (e.g. staff-assisted sign-up).
        if password:
            user.set_password(password)
            user.save()
        elif created:
            user.set_unusable_password()
            user.save()

        parsed_dob = None
        parsed_age = None
        if date_of_birth:
            try:
                parsed_dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                parsed_age = calculate_age(parsed_dob)
            except ValueError:
                parsed_dob = None

        # Create or get patient profile
        patient, created_patient = Patient.objects.get_or_create(user=user, defaults={
            'date_of_birth': parsed_dob,
            'age': parsed_age,
            'blood_type': blood_type,
            'allergies': allergies,
            'address': address,
            'contact_number': phone,
            'emergency_contact': emergency_contact,
            'emergency_contact_relationship': relationship,
            'symptoms': symptoms,
            'existing_conditions': existing_conditions,
            'current_medications': current_medications,
            'medical_history': medical_history,
        })

        # Update contact and symptoms if provided
        updated = False
        if parsed_dob and patient.date_of_birth != parsed_dob:
            patient.date_of_birth = parsed_dob
            patient.age = parsed_age
            updated = True
        if blood_type and patient.blood_type != blood_type:
            patient.blood_type = blood_type
            updated = True
        if allergies and patient.allergies != allergies:
            patient.allergies = allergies
            updated = True
        if address and patient.address != address:
            patient.address = address
            updated = True
        if phone and (not patient.contact_number or patient.contact_number != phone):
            patient.contact_number = phone
            updated = True
        if emergency_contact and patient.emergency_contact != emergency_contact:
            patient.emergency_contact = emergency_contact
            updated = True
        if relationship and patient.emergency_contact_relationship != relationship:
            patient.emergency_contact_relationship = relationship
            updated = True
        if symptoms and (not patient.symptoms or patient.symptoms != symptoms):
            patient.symptoms = symptoms
            updated = True
        if existing_conditions and patient.existing_conditions != existing_conditions:
            patient.existing_conditions = existing_conditions
            updated = True
        if current_medications and patient.current_medications != current_medications:
            patient.current_medications = current_medications
            updated = True
        if medical_history and patient.medical_history != medical_history:
            patient.medical_history = medical_history
            updated = True
        if updated:
            patient.save()

        # Ensure a VirtualCard exists
        try:
            _ = patient.virtual_card
        except ObjectDoesNotExist:
            from .models import VirtualCard
            vc = VirtualCard(patient=patient)
            vc.save()

        # Log the patient in automatically when they set a password.
        if password and not request.user.is_authenticated:
            auth_user = authenticate(request, username=user.username, password=password)
            if auth_user is not None:
                login(request, auth_user)

        # Use explicit path to avoid any reverse/name issues
        return redirect(f'/patient/{patient.pk}/dashboard/')

    return render(request, 'patient/register.html')
def patient_virtual_card(request, patient_id):
    patient = get_object_or_404(Patient.objects.select_related('user'), pk=patient_id)

    # Attach the user-facing fields the template expects.
    patient.first_name = getattr(patient.user, 'first_name', '')
    patient.last_name = getattr(patient.user, 'last_name', '')
    patient.email = getattr(patient.user, 'email', '')

    try:
        vc = patient.virtual_card
        patient.virtual_card_id = getattr(vc, 'virtual_card_id', '')
        patient.qr_code = getattr(vc, 'qr_code', None)
    except ObjectDoesNotExist:
        patient.virtual_card_id = ''
        patient.qr_code = None

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
