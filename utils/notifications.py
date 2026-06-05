from django.core.mail import send_mail
from django.conf import settings
import logging
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def _resolve_user(subject):
    if subject is None:
        return None

    if isinstance(subject, User):
        return subject

    if hasattr(subject, 'user') and isinstance(getattr(subject, 'user', None), User):
        return subject.user

    if isinstance(subject, int):
        return User.objects.filter(pk=subject).first()

    return None


def _create_notification(recipient, message):
    from queue_app.models import Notification

    user = _resolve_user(recipient)
    if not user:
        return None

    return Notification.objects.create(recipient=user, message=message)

def send_notification(doctor, patient, message):
    """Send notification to doctor about new patient"""
    try:
        doctor_user = _resolve_user(doctor)
        patient_user = _resolve_user(patient)

        if doctor_user:
            _create_notification(doctor_user, message)

        if doctor_user:
            doctor_name = doctor_user.get_full_name() or doctor_user.username
        else:
            doctor_name = str(doctor)

        # In production, this would integrate with hospital notification system
        logger.info(f"Doctor Notification - Dr. {doctor_name}: {message}")
        
        # Example: Send email notification
        patient_name = ""
        if patient_user:
            patient_name = patient_user.get_full_name() or patient_user.username
        elif hasattr(patient, 'user'):
            patient_name = patient.user.get_full_name() or patient.user.username

        subject = f"New Patient - {patient_name}" if patient_name else "New Patient"
        email_message = f"""
        Dear Dr. {doctor_name},
        
        New patient arrived:
        - Name: {patient_name}
        - Priority: {getattr(patient, 'priority', 'Routine')}
        - Department: {getattr(getattr(doctor, 'department', None), 'name', 'N/A')}
        
        {message}
        
        Please check your dashboard for details.
        
        Best regards,
        AI Queueing System
        """
        
        # Uncomment to send actual email
        # send_mail(
        #     subject,
        #     email_message,
        #     settings.DEFAULT_FROM_EMAIL,
        #     [doctor.user.email],
        #     fail_silently=False,
        # )
        
        return True
        
    except Exception as e:
        logger.error(f"Doctor notification error: {e}")
        return False

def send_patient_notification(patient, message_type, additional_data=None):
    """Send notification to patient"""
    try:
        if additional_data is None:
            additional_data = {}

        patient_user = _resolve_user(patient)
        patient_name = ""
        if patient_user:
            patient_name = patient_user.get_full_name() or patient_user.username
        elif hasattr(patient, 'user'):
            patient_name = patient.user.get_full_name() or patient.user.username
        
        messages = {
            'registration_success': f"Welcome {patient_name or 'there'}! Your virtual card is ready.",
            'queue_update': f"Your queue position has been updated.",
            'doctor_assigned': f"Dr. {additional_data.get('doctor_name', '')} has been assigned to you.",
            'consultation_ready': "Please proceed to the consultation room.",
            'prescription_ready': "Your prescription is ready for collection.",
        }
        
        message = messages.get(message_type, "Notification from hospital")

        if patient_user:
            _create_notification(patient_user, message)
        
        # Send SMS if phone number available
        phone_number = getattr(patient, 'phone_number', None) or getattr(patient, 'contact_number', None)
        if phone_number:
            from .helpers import send_sms_notification
            send_sms_notification(phone_number, message)
        
        logger.info(f"Patient Notification - {patient_name or patient}: {message}")
        return True
        
    except Exception as e:
        logger.error(f"Patient notification error: {e}")
        return False

def send_emergency_alert(patient, condition):
    """Send emergency alert to medical staff"""
    try:
        patient_user = _resolve_user(patient)
        patient_name = ""
        if patient_user:
            patient_name = patient_user.get_full_name() or patient_user.username
        elif hasattr(patient, 'user'):
            patient_name = patient.user.get_full_name() or patient.user.username

        alert_message = f"""
        EMERGENCY ALERT
        Patient: {patient_name}
        Condition: {condition}
        Location: Waiting Area
        Priority: IMMEDIATE ATTENTION REQUIRED
        """
        
        logger.error(f"EMERGENCY: {alert_message}")
        
        # In production, this would trigger hospital emergency protocols
        return True
        
    except Exception as e:
        logger.error(f"Emergency alert error: {e}")
        return False

def broadcast_queue_update(department, current_ticket):
    """Broadcast queue update to all connected clients"""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from queue_app.models import Notification
        from django.contrib.auth.models import User
        
        channel_layer = get_channel_layer()

        update_message = (
            f"Queue updated for {department.name}: {current_ticket.ticket_number} "
            f"- {current_ticket.patient.user.get_full_name() or current_ticket.patient.user.username}"
        )

        staff_recipients = User.objects.filter(is_staff=True)
        if not staff_recipients.exists():
            staff_recipients = User.objects.filter(is_superuser=True)

        for user in staff_recipients:
            Notification.objects.create(recipient=user, message=update_message)
        
        async_to_sync(channel_layer.group_send)(
            f"department_{department.id}",
            {
                "type": "queue_update",
                "message": {
                    "current_ticket": current_ticket.ticket_number,
                    "patient_name": current_ticket.patient.user.get_full_name() or current_ticket.patient.user.username,
                    "department": department.name,
                    "message": update_message,
                }
            }
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Queue broadcast error: {e}")
        return False