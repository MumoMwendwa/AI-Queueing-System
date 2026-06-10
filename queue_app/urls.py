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
    login_page,
    patient_login,
    patient_register,
    doctor_login,
    logout_view,
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

    # Auth
    path('', login_page, name='login'),
    path('register/', patient_register, name='patient_register'),
    path('login/patient/', patient_login, name='patient_login'),
    path('login/doctor/', doctor_login, name='doctor_login'),
    path('logout/', logout_view, name='logout'), 

    # Main
    path('home/', home, name='home'),

    # Doctor portal
    path('doctor/', doctor_dashboard, name='doctor_home'),
    path('doctor/dashboard/', doctor_dashboard, name='doctor_dashboard'),
    path('doctor/notifications/', doctor_notifications, name='doctor_notifications'),
    path('doctor/consultation/<int:ticket_id>/', doctor_consultation, name='doctor_consultation'),
    path('doctor/patient/<int:patient_id>/', doctor_patient_detail, name='doctor_patient'),


    #REST API 
    path('api/', include(router.urls)), 

    # AI API routes
    path('api/patient/check-in/', ai_views.api_patient_check_in, name='api_patient_check_in'),
    path('api/ai/triage/', ai_views.ai_triage_assessment, name='ai_triage'),
    path('api/ai/wait-time/<int:department_id>/', ai_views.ai_wait_time_prediction, name='ai_wait_time'),
    path('api/ai/patient-flow/', ai_views.ai_patient_flow_prediction, name='ai_patient_flow'),
    path('api/ai/medical-analysis/<str:patient_id>/', ai_views.ai_medical_analysis, name='ai_medical_analysis'),
    path('api/ai/drug-interaction-check/', ai_views.ai_drug_interaction_check, name='ai_drug_interaction'),
]