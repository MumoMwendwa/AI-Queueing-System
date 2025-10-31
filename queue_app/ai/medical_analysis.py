# queue_app/ai/medical_analysis.py
class MedicalAnalysis:
    def analyze_vitals(self, vitals):
        """
        Check if vitals are normal or abnormal.
        vitals = {'bp': 120, 'pulse': 80, 'temp': 37.5}
        """
        report = {}
        bp = vitals.get('bp', 120)
        pulse = vitals.get('pulse', 80)
        temp = vitals.get('temp', 37)

        report['bp_status'] = 'high' if bp > 130 else 'low' if bp < 90 else 'normal'
        report['pulse_status'] = 'high' if pulse > 100 else 'low' if pulse < 60 else 'normal'
        report['temp_status'] = 'fever' if temp > 38 else 'normal'

        return report

    def summary(self, vitals):
        report = self.analyze_vitals(vitals)
        if any(val != 'normal' for val in report.values()):
            return "Abnormal vitals detected, recommend doctor review."
        return "Patient vitals appear normal."
