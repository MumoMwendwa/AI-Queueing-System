# urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DoctorViewSet,
    PatientViewSet,
    QueueViewSet,
    NotificationViewSet,
    QueueTicketViewSet,
    doctor_consultation,
    doctor_dashboard,
    doctor_notifications,
    doctor_patient_detail,
    home,
)
from . import ai_views
# Create a router to automatically handle all viewset URLs
router = DefaultRouter()
router.register(r'doctors', DoctorViewSet)
router.register(r'patients', PatientViewSet)
router.register(r'queues', QueueViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'queue-tickets', QueueTicketViewSet)



urlpatterns = [
    # Include all the router-generated routes
    path('', include(router.urls)),
    path('', home, name='home'),

    # Doctor portal
    path('doctor/', doctor_dashboard, name='doctor_home'),
    path('doctor/dashboard/', doctor_dashboard, name='doctor_dashboard'),
    path('doctor/notifications/', doctor_notifications, name='doctor_notifications'),
    path('doctor/consultation/<int:ticket_id>/', doctor_consultation, name='doctor_consultation'),
    path('doctor/patient/<int:patient_id>/', doctor_patient_detail, name='doctor_patient'),

     # API routes
    path('api/patient/check-in/', ai_views.api_patient_check_in, name='api_patient_check_in'),
    
    # AI API routes
    path('api/ai/triage/', ai_views.ai_triage_assessment, name='ai_triage'),
    path('api/ai/wait-time/<int:department_id>/', ai_views.ai_wait_time_prediction, name='ai_wait_time'),
    path('api/ai/patient-flow/', ai_views.ai_patient_flow_prediction, name='ai_patient_flow'),
    path('api/ai/medical-analysis/<str:patient_id>/', ai_views.ai_medical_analysis, name='ai_medical_analysis'),
    path('api/ai/drug-interaction-check/', ai_views.ai_drug_interaction_check, name='ai_drug_interaction'),
]

