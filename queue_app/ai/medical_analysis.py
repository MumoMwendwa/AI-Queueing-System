# queue_app/ai/medical_analysis.py
import joblib
import os
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

class MedicalAnalysis:
    def __init__(self):
        self.symptoms = ["fever", "cough", "fatigue", "headache", "pain"]
        self.model_path = os.path.join(os.path.dirname(__file__), 'models', 'medical_analysis.pkl')
        self.model = None

    def _encode_symptoms(self, patient_symptoms):
        return [1 if s in patient_symptoms else 0 for s in self.symptoms]

    def analyze(self, patient_symptoms):
        """
        Predict possible condition based on patient symptoms.
        """
        if self.model:
            X = np.array([self._encode_symptoms(patient_symptoms)])
            return self.model.predict(X)[0]
        else:
            return "Possible mild condition"

    def train_model(self):
        """
        Train a dummy Naive Bayes classifier for medical condition prediction.
        """
        print("🧠 Training Medical Analysis model...")

        # Dummy dataset
        X = np.array([
            [1,1,0,0,0],  # fever + cough
            [0,0,1,1,0],  # fatigue + headache
            [0,0,0,1,1],  # headache + pain
            [1,1,1,0,0],  # fever + cough + fatigue
        ])
        y = np.array(["flu", "migraine", "injury", "infection"])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
        model = MultinomialNB()
        model.fit(X_train, y_train)
        acc = model.score(X_test, y_test)

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(model, self.model_path)
        self.model = model

        print(f"✅ Medical analysis model trained (accuracy: {acc:.2f})")
        return acc

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print("📦 Loaded Medical Analysis model.")
        else:
            print("⚠️ No trained model found.")
