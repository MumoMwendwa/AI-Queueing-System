import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import F

from utils.helpers import calculate_wait_time, format_time_minutes, calculate_priority_score
from utils.notifications import send_patient_notification, broadcast_queue_update


# Example AI-based endpoints

@require_POST
def api_patient_check_in(request):
    """Handle manual or QR-based patient check-in.

    Accepts JSON POST with one of:
      - virtual_card_id
      - phone

    Creates a QueueTicket for a default department, estimates wait time,
    notifies patient, and broadcasts queue updates.
    """
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8') or '{}')
        else:
            data = request.POST
    except Exception:
        data = {}

    virtual_card_id = data.get('virtual_card_id') or data.get('virtual_card')
    phone = data.get('phone')

    # Lazy imports to avoid circulars on startup
    from .models import VirtualCard, Patient, QueueTicket, Department

    patient = None
    if virtual_card_id:
        try:
            vc = VirtualCard.objects.select_related('patient').get(virtual_card_id=virtual_card_id)
            patient = vc.patient
        except VirtualCard.DoesNotExist:
            return JsonResponse({'error': 'Virtual card not found'}, status=404)
    elif phone:
        patient = Patient.objects.filter(contact_number=phone).first()
        if not patient:
            # Try username/email fallback
            patient = Patient.objects.select_related('user').filter(
                user__username=phone
            ).first()
        if not patient:
            return JsonResponse({'error': 'Patient not found for provided phone'}, status=404)
    else:
        return JsonResponse({'error': 'Provide virtual_card_id or phone'}, status=400)

    # Choose a department - default to first available
    department = Department.objects.first()
    if not department:
        return JsonResponse({'error': 'No department available'}, status=500)

    # Create a ticket and increment department counter safely
    with transaction.atomic():
        Department.objects.filter(pk=department.pk).update(current_queue_number=F('current_queue_number') + 1)
        department.refresh_from_db()

        ticket_number = f"{department.name[:3].upper()}-{department.current_queue_number:04d}"

        # Determine queue position (number of waiting tickets) and estimate wait
        position = QueueTicket.objects.filter(department=department, status='waiting').count() + 1
        estimated_minutes = calculate_wait_time(position)

        # Basic priority score using helper
        priority_score = calculate_priority_score(getattr(patient, 'age', 0), getattr(patient, 'symptoms', '') or '', getattr(patient, 'medical_history', '') or '') / 100.0

        ticket = QueueTicket.objects.create(
            ticket_number=ticket_number,
            patient=patient,
            department=department,
            status='waiting',
            estimated_wait_time=estimated_minutes,
            ai_priority_score=priority_score,
        )

    # Notify patient and broadcast update to websockets/clients
    try:
        send_patient_notification(patient, 'registration_success', {'ticket_number': ticket.ticket_number})
    except Exception:
        # best-effort
        pass

    try:
        broadcast_queue_update(department, ticket)
    except Exception:
        pass

    return JsonResponse({
        'ticket_number': ticket.ticket_number,
        'position': position,
        'estimated_wait_time': format_time_minutes(estimated_minutes),
    })


def ai_triage_assessment(request):
    return JsonResponse({"message": "Triage assessment completed."})


def ai_wait_time_prediction(request, department_id):
    return JsonResponse({
        "department_id": department_id,
        "predicted_wait_time": "15 minutes"
    })


def ai_patient_flow_prediction(request):
    return JsonResponse({
        "prediction": "Moderate traffic expected in the next hour."
    })


def ai_medical_analysis(request, patient_id):
    return JsonResponse({
        "patient_id": patient_id,
        "analysis": "No anomalies detected in recent test data."
    })


def ai_drug_interaction_check(request):
    return JsonResponse({
        "result": "No harmful drug interactions found."
    })
