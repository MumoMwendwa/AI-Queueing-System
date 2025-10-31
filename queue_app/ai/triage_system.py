# queue_app/ai/triage_system.py
class TriageSystem:
    def __init__(self):
        self.rules = {
            'chest pain': 'critical',
            'fever': 'moderate',
            'headache': 'mild',
            'bleeding': 'critical',
            'cough': 'mild',
        }

    def assess_patient(self, symptoms):
        """
        Classify patient severity based on symptoms.
        """
        severity_levels = [self.rules.get(symptom.lower(), 'moderate') for symptom in symptoms]
        if 'critical' in severity_levels:
            return 'critical'
        elif 'moderate' in severity_levels:
            return 'moderate'
        return 'mild'
