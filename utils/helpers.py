import re
from datetime import datetime, timedelta
from django.utils import timezone
import random
import string

def calculate_wait_time(queue_position, avg_consultation_time=15):
    """Calculate estimated wait time based on queue position"""
    return queue_position * avg_consultation_time

def validate_phone_number(phone_number):
    """Validate phone number format"""
    pattern = r'^\+?1?\d{9,15}$'
    return re.match(pattern, phone_number) is not None

def generate_random_string(length=8):
    """Generate random string for temporary codes"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def format_time_minutes(minutes):
    """Format minutes into human-readable time"""
    if minutes < 60:
        return f"{minutes} minutes"
    else:
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours} hours {mins} minutes" if mins > 0 else f"{hours} hours"

def calculate_age(date_of_birth):
    """Calculate age from date of birth"""
    today = timezone.now().date()
    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

def is_working_hours():
    """Check if current time is within hospital working hours"""
    now = timezone.now()
    hour = now.hour
    # Hospital hours: 8 AM to 8 PM
    return 8 <= hour < 20

def get_next_available_time():
    """Get next available appointment time"""
    now = timezone.now()
    if is_working_hours():
        # If within working hours, next available is in 30 minutes
        return now + timedelta(minutes=30)
    else:
        # If outside working hours, next available is next day at 8 AM
        next_day = now + timedelta(days=1)
        return next_day.replace(hour=8, minute=0, second=0, microsecond=0)

def send_sms_notification(phone_number, message):
    """Send SMS notification to patient (placeholder implementation)"""
    # In production, integrate with SMS service like Twilio
    print(f"SMS to {phone_number}: {message}")
    return True

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    if not text:
        return ""
    # Basic sanitization - replace potentially dangerous characters
    sanitized = text.replace('<', '&lt;').replace('>', '&gt;')
    sanitized = sanitized.replace('"', '&quot;').replace("'", '&#x27;')
    return sanitized

def generate_emergency_code():
    """Generate emergency code for critical situations"""
    return f"EMG-{generate_random_string(6)}"

def calculate_priority_score(age, symptoms, existing_conditions):
    """Calculate priority score for patient"""
    score = 0
    
    # Age factor - children and elderly get higher priority
    if age <= 12 or age >= 65:
        score += 20
    
    # Symptom severity
    emergency_symptoms = ['chest pain', 'bleeding', 'unconscious', 'difficulty breathing']
    urgent_symptoms = ['fever', 'pain', 'vomiting', 'injury']
    
    if any(symptom in symptoms.lower() for symptom in emergency_symptoms):
        score += 50
    elif any(symptom in symptoms.lower() for symptom in urgent_symptoms):
        score += 30
    
    # Existing conditions
    if existing_conditions:
        score += 10
    
    return min(100, score)