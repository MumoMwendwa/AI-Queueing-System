# queue_app/views.py

from datetime import timedelta
from functools import wraps
from datetime import datetime
from types import SimpleNamespace

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from rest_framework import viewsets

from .models import Doctor, Patient, Queue, Notification, Department, QueueTicket
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
    patient = None
    departments = Department.objects.all()
    department_data = []

    for department in departments:
        in_consultation_ticket = department.queueticket_set.filter(
            status='in_consultation'
        ).first()

        waiting_tickets = department.queueticket_set.filter(
            status='waiting'
        ).order_by('ticket_number')[:5]

        department_data.append({
            'name': department.name,
            'current_ticket': in_consultation_ticket,
            'waiting_list': waiting_tickets,
        })

    return render(request, 'home.html', {
        'departments': department_data,
        'system_title': "AI Queueing Display"

    })


# ──────────────────────────────────────────
# AUTH VIEWS
# ──────────────────────────────────────────

def login_page(request):
    """Main login page — redirects already-authenticated users straight to their dashboard."""
    if request.user.is_authenticated:
        if get_doctor_profile(request):
            return redirect('doctor_dashboard')
        # Try to find a patient linked to this user
        try:
            patient = request.user.patient
            return redirect('patient_dashboard', patient_id=patient.pk)
        except ObjectDoesNotExist:
            pass
    role = request.GET.get('role', 'patient')
    return render(request, 'login.html', {'role': role})


def patient_login(request):
    """Handles patient login form submission."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # Django's default auth uses username; look up the user by email first
        try:
            username = User.objects.get(email=email).username
        except User.DoesNotExist:
            username = email  # fallback — try email as username

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            try:
                patient = user.patient
                return redirect('patient_dashboard', patient_id=patient.pk)
            except ObjectDoesNotExist:
                messages.error(request, 'No patient profile found for this account.')
        else:
            messages.error(request, 'Invalid email or password. Please try again.')

    return redirect(reverse('login') + '?role=patient')


def doctor_login(request):
    """Handles doctor login form submission."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Support login by email as well as staff ID / username
        if '@' in username:
            try:
                username = User.objects.get(email=username).username
            except User.DoesNotExist:
                pass

        user = authenticate(request, username=username, password=password)

        if user is not None and get_doctor_profile_for_user(user):
            login(request, user)
            return redirect('doctor_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not a doctor account.')

    return redirect(reverse('login') + '?role=doctor')


def logout_view(request):
    """Logs out any user and returns to the login page."""
    logout(request)
    return redirect('login')


def get_doctor_profile_for_user(user):
    """Helper used during login before the request object is fully set up."""
    try:
        return user.doctor_profile
    except ObjectDoesNotExist:
        return None


# ──────────────────────────────────────────
# PATIENT VIEWS
# ──────────────────────────────────────────

def patient_dashboard(request, patient_id):
    patient = get_object_or_404(Patient.objects.select_related('user'), pk=patient_id)

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

    current_ticket = (
        QueueTicket.objects.filter(patient=patient, status__in=['waiting', 'in_consultation'])
        .select_related('department', 'doctor')
        .order_by('-check_in_time')
        .first()
    )

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
    if request.method == 'POST':
        # Validating Passwords. 
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if password != confirm_password:
            messages.error(request, 'Passwords do not match. Please try again.')
            return render(request, 'patient/register.html')
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'patient/register.html')
        
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
        password = request.POST.get('password', '').strip()

        medical_history_parts = [
            f"Symptoms: {symptoms}" if symptoms else "",
            f"Existing Conditions: {existing_conditions}" if existing_conditions else "",
            f"Current Medications: {current_medications}" if current_medications else "",
        ]
        medical_history = "\n".join(part for part in medical_history_parts if part)

        username = email or phone or f'user_{User.objects.count() + 1}'

        try:
            user, created = User.objects.get_or_create(username=username, defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
            })
        except IntegrityError:
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

        # Set a real password so the patient can log in next time
        if password:
            user.set_password(password)
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

        try:
            _ = patient.virtual_card
        except ObjectDoesNotExist:
            from .models import VirtualCard
            vc = VirtualCard(patient=patient)
            vc.save()

        # Log the new patient in automatically after registration
        if password and created:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)

        return redirect(f'/patient/{patient.pk}/dashboard/')

    return render(request, 'patient/register.html')


def patient_virtual_card(request, patient_id):
    patient = get_object_or_404(Patient.objects.select_related('user'), pk=patient_id)

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


# ──────────────────────────────────────────
# DOCTOR VIEWS
# ──────────────────────────────────────────

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


# ──────────────────────────────────────────
# VIEWSETS
# ──────────────────────────────────────────

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