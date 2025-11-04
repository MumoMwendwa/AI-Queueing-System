# queue_app/views.py

from rest_framework import viewsets
from .models import Doctor, Patient, Queue, Notification, Department, QueueTicket # 👈 Make sure to import ALL necessary models
from .serializers import DoctorSerializer, PatientSerializer, QueueSerializer, NotificationSerializer, QueueTicketSerializer
from django.shortcuts import render

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
        
    # 4. Create the context dictionary
    context = {
        'departments': department_data,
        # You can add other global variables here
        'system_title': "AI Queueing Display",
        'patient' : patient, 
    }
    
    return render(request, 'base.html', context)

def patient_dashboard(request, patient_id):
    # Logic for patient dashboard view
    return render(request, 'patient/dashboard.html')
def patient_register(request):
    # Logic for patient registration view
    return render(request, 'patient/register.html')
def patient_virtual_card(request, patient_id):
    # Logic for patient virtual card view
    return render(request, 'patient/virtual_card.html')


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
