# queue_app/ai/notification_system.py
from utils.notifications import send_notification  # example helper


class NotificationSystem:
    def notify_patient(self, patient_id, message):
        """
        Send queue updates or reminders to a patient.
        """
        return send_notification(patient_id, message)

    def notify_doctor(self, doctor_id, message):
        """
        Notify doctor when patient is ready or emergency detected.
        """
        return send_notification(doctor_id, message)
