import qrcode
from io import BytesIO
from django.core.files import File
import uuid
from PIL import Image, ImageDraw
import os
from django.conf import settings

def generate_qr_code(data, patient_id=None):
    """Generate QR code for patient virtual card"""
    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Add data to QR code
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to BytesIO
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        
        # Create file name
        if patient_id:
            filename = f'qr_{patient_id}.png'
        else:
            filename = f'qr_{uuid.uuid4().hex[:8]}.png'
        
        # Return file object
        return File(buffer, filename)
        
    except Exception as e:
        print(f"QR generation error: {e}")
        return None

def generate_virtual_card_id():
    """Generate unique virtual card ID for patient"""
    return f"VC-{uuid.uuid4().hex[:12].upper()}"

def create_patient_qr_data(patient_data):
    """Create QR code data string from patient information"""
    required_fields = ['virtual_card_id', 'patient_id', 'first_name', 'last_name']
    
    # Validate required fields
    for field in required_fields:
        if field not in patient_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Create structured data string
    qr_data = f"""
    PATIENT CARD
    ID: {patient_data['virtual_card_id']}
    Patient: {patient_data['patient_id']}
    Name: {patient_data['first_name']} {patient_data['last_name']}
    Hospital: AI Queueing System
    Emergency: Call 911
    """
    
    return qr_data.strip()

def generate_qr_with_logo(data, logo_path=None):
    """Generate QR code with hospital logo in center"""
    try:
        # Generate basic QR code
        qr = qrcode.QRCode(
            version=5,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        
        # Add logo if provided
        if logo_path and os.path.exists(logo_path):
            logo = Image.open(logo_path)
            
            # Calculate logo size (20% of QR code size)
            qr_width, qr_height = qr_image.size
            logo_size = min(qr_width, qr_height) // 5
            
            # Resize logo
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Calculate position to center logo
            pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
            
            # Create a white background for logo
            logo_bg = Image.new('RGB', (logo_size, logo_size), 'white')
            logo_bg.paste(logo, (0, 0))
            
            # Paste logo on QR code
            qr_image.paste(logo_bg, pos)
        
        # Convert to BytesIO
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        
        return File(buffer, 'qr_with_logo.png')
        
    except Exception as e:
        print(f"QR with logo generation error: {e}")
        return generate_qr_code(data)  # Fallback to basic QR

def validate_qr_data(qr_data):
    """Validate QR code data format"""
    try:
        lines = qr_data.strip().split('\n')
        if len(lines) < 3:
            return False
        
        # Check for required identifiers
        required_identifiers = ['PATIENT CARD', 'ID:', 'Patient:']
        for identifier in required_identifiers:
            if not any(identifier in line for line in lines):
                return False
        
        return True
    except:
        return False

def parse_qr_data(qr_data):
    """Parse QR code data and extract patient information"""
    if not validate_qr_data(qr_data):
        return None
    
    try:
        lines = qr_data.strip().split('\n')
        patient_info = {}
        
        for line in lines:
            if 'ID:' in line:
                patient_info['virtual_card_id'] = line.split('ID:')[1].strip()
            elif 'Patient:' in line:
                patient_info['patient_id'] = line.split('Patient:')[1].strip()
            elif 'Name:' in line:
                name_parts = line.split('Name:')[1].strip().split()
                if len(name_parts) >= 2:
                    patient_info['first_name'] = name_parts[0]
                    patient_info['last_name'] = ' '.join(name_parts[1:])
        
        return patient_info if patient_info else None
        
    except Exception as e:
        print(f"QR data parsing error: {e}")
        return None

def generate_emergency_qr(patient_data):
    """Generate emergency QR code with critical patient information"""
    emergency_data = f"""
    EMERGENCY MEDICAL INFORMATION
    Patient: {patient_data.get('first_name', '')} {patient_data.get('last_name', '')}
    ID: {patient_data.get('patient_id', '')}
    Virtual Card: {patient_data.get('virtual_card_id', '')}
    Blood Type: {patient_data.get('blood_type', 'Unknown')}
    Allergies: {patient_data.get('allergies', 'None')}
    Emergency Contact: {patient_data.get('emergency_contact', '')}
    Hospital: AI Queueing System
    """
    
    return generate_qr_code(emergency_data.strip())