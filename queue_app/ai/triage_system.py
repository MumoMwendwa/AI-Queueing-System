# queue_app/ai/triage_system.py
import joblib
import os
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

class TriageSystem:
    def __init__(self):
        self.rules = {
            'chest pain': 'critical',
            'fever': 'moderate',
            'headache': 'mild',
            'bleeding': 'critical',
            'cough': 'mild',
        }
        self.model_path = os.path.join(os.path.dirname(__file__), 'models', 'triage_model.pkl')
        self.model = None

    def assess_patient(self, symptoms):
        """
        Classify patient severity based on symptoms or trained model.
        """
        # Try ML model first
        if self.model is not None:
            X = np.array([self._encode_symptoms(symptoms)])
            prediction = self.model.predict(X)[0]
            return prediction

        # Fallback to rule-based logic
        severity_levels = [self.rules.get(symptom.lower(), 'moderate') for symptom in symptoms]
        if 'critical' in severity_levels:
            return 'critical'
        elif 'moderate' in severity_levels:
            return 'moderate'
        return 'mild'

    def _encode_symptoms(self, symptoms):
        """
        Convert symptoms into numeric features for ML model.
        """
        all_symptoms = list(self.rules.keys())
        return [1 if s in symptoms else 0 for s in all_symptoms]

    def train_model(self):
        """
        Simulate training a triage model with dummy data.
        """
        print("🧠 Training triage system model...")

        # Dummy data: list of symptom combinations and corresponding severity
        X = []
        y = []
        for symptom, severity in self.rules.items():
            encoded = self._encode_symptoms([symptom])
            X.append(encoded)
            y.append(severity)

        # Add some random combos for diversity
        extra_data = [
            (['fever', 'cough'], 'moderate'),
            (['headache', 'cough'], 'mild'),
            (['bleeding', 'chest pain'], 'critical')
        ]
        for symptoms, severity in extra_data:
            X.append(self._encode_symptoms(symptoms))
            y.append(severity)

        X = np.array(X)
        y = np.array(y)

        # Split & train
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        acc = model.score(X_test, y_test)

        # Save model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(model, self.model_path)
        self.model = model

        print(f"✅ Triage model trained successfully with accuracy: {acc:.2f}")
        return acc

    def load_model(self):
        """
        Load trained model if available.
        """
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print("📦 Loaded trained triage model.")
        else:
            print("⚠️ No trained model found. Using rule-based system.")
