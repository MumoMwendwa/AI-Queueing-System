import requests
import json
from django.conf import settings

class AITriageSystem:
    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
    
    def analyze_symptoms(self, symptoms_text):
        """Analyze patient symptoms using AI"""
        if not self.api_key:
            return self.fallback_triage(symptoms_text)
        
        try:
            # Using OpenAI API for symptom analysis
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={'Authorization': f'Bearer {self.api_key}'},
                json={
                    'model': 'gpt-3.5-turbo',
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are a medical triage assistant. Analyze symptoms and suggest priority level and department.'
                        },
                        {
                            'role': 'user', 
                            'content': f"Symptoms: {symptoms_text}. Provide analysis in JSON format with priority, suggested_department, and confidence."
                        }
                    ]
                }
            )
            
            if response.status_code == 200:
                return self.parse_ai_response(response.json())
            else:
                return self.fallback_triage(symptoms_text)
                
        except Exception as e:
            print(f"AI Triage error: {e}")
            return self.fallback_triage(symptoms_text)
    
    def fallback_triage(self, symptoms_text):
        """Fallback rule-based triage when AI is unavailable"""
        symptoms_lower = symptoms_text.lower()
        
        # Basic rule-based triage
        emergency_keywords = ['chest pain', 'difficulty breathing', 'severe bleeding', 'unconscious']
        urgent_keywords = ['fever', 'pain', 'vomiting', 'injury']
        
        if any(keyword in symptoms_lower for keyword in emergency_keywords):
            return {'priority': 'emergency', 'suggested_department': 'Emergency', 'confidence': 0.8}
        elif any(keyword in symptoms_lower for keyword in urgent_keywords):
            return {'priority': 'urgent', 'suggested_department': 'General Medicine', 'confidence': 0.7}
        else:
            return {'priority': 'routine', 'suggested_department': 'General Medicine', 'confidence': 0.6}