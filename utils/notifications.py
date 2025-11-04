from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_notification(doctor, patient, message):
    """Send notification to doctor about new patient"""
    try:
        # In production, this would integrate with hospital notification system
        logger.info(f"Doctor Notification - Dr. {doctor.name}: {message}")
        
        # Example: Send email notification
        subject = f"New Patient - {patient.first_name} {patient.last_name}"
        email_message = f"""
        Dear Dr. {doctor.name},
        
        New patient arrived:
        - Name: {patient.first_name} {patient.last_name}
        - Priority: {getattr(patient, 'priority', 'Routine')}
        - Department: {doctor.department.name}
        
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
        
        messages = {
            'registration_success': f"Welcome {patient.first_name}! Your virtual card is ready.",
            'queue_update': f"Your queue position has been updated.",
            'doctor_assigned': f"Dr. {additional_data.get('doctor_name', '')} has been assigned to you.",
            'consultation_ready': "Please proceed to the consultation room.",
            'prescription_ready': "Your prescription is ready for collection.",
        }
        
        message = messages.get(message_type, "Notification from hospital")
        
        # Send SMS if phone number available
        if patient.phone_number:
            from .helpers import send_sms_notification
            send_sms_notification(patient.phone_number, message)
        
        logger.info(f"Patient Notification - {patient.patient_id}: {message}")
        return True
        
    except Exception as e:
        logger.error(f"Patient notification error: {e}")
        return False

def send_emergency_alert(patient, condition):
    """Send emergency alert to medical staff"""
    try:
        alert_message = f"""
        EMERGENCY ALERT
        Patient: {patient.first_name} {patient.last_name}
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
        
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f"department_{department.id}",
            {
                "type": "queue_update",
                "message": {
                    "current_ticket": current_ticket.ticket_number,
                    "patient_name": f"{current_ticket.patient.first_name} {current_ticket.patient.last_name}",
                    "department": department.name
                }
            }
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Queue broadcast error: {e}")
        return False