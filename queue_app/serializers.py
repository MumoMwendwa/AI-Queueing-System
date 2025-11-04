# serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Doctor, Patient, Queue, Notification, QueueTicket, Department

#
# 1 USER SERIALIZER ; this serializer converts Django User model data into JSON format
# used for displaying or receiving user information through the API.
#
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

#
# 2 DOCTOR SERIALIZER ; this serializer handles the conversion of doctor data to and from JSON
# allows the API to send doctor details to the frontend or receive new data from it.
#
class DoctorSerializer(serializers.ModelSerializer):
    # Include user details inside the doctor serializer
    user = UserSerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'specialization', 'room_number', 'is_available']

#
# 3 PATIENT SERIALIZER ; this serializer converts patient data for API communication
# used for registering patients, showing their profile, and updating their information.
#
class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Patient
        fields = [
            'id', 'user', 'age', 'contact_number', 'emergency_contact',
            'medical_history', 'gender', 'symptoms', 'registered_at'
        ]

#
# 4 QUEUE SERIALIZER ; this serializer manages queue data exchange between backend and frontend
# includes patient and doctor info for easy display of who is next in line.
#
class QueueSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)

    class Meta:
        model = Queue
        fields = [
            'id', 'patient', 'doctor', 'status',
            'created_at', 'updated_at', 'predicted_wait_time'
        ]

#
# 5 NOTIFICATION SERIALIZER ; handles sending notification details in JSON format
# used for pushing alerts to patients or doctors about queue updates.
#
class NotificationSerializer(serializers.ModelSerializer):
    recipient = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'message', 'created_at', 'is_read']

#
# 6 QUEUE TICKET SERIALIZER ; this serializer converts queue ticket data for API communication
# used for managing queue tickets, including patient, department, and doctor details.
#
class QueueTicketSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    department = serializers.StringRelatedField(read_only=True)  # Or create a DepartmentSerializer if needed
    doctor = DoctorSerializer(read_only=True)

    class Meta:
        model = QueueTicket
        fields = [
            'id', 'ticket_number', 'patient', 'department', 'doctor', 'status',
            'check_in_time', 'consultation_start_time', 'consultation_end_time',
            'estimated_wait_time', 'ai_priority_score', 'predicted_consultation_time',
            'ai_suggested_doctor', 'symptom_analysis'
        ]
