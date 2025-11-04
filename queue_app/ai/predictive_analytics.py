# queue_app/ai/predictive_analytics.py
import joblib
import os
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

class PredictiveAnalytics:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), 'models', 'predictive_model.pkl')
        self.model = None

    def predict_queue_length(self, current_patients, avg_service_time):
        """
        Predict queue length based on current patients and service time.
        """
        if self.model:
            X = np.array([[current_patients, avg_service_time]])
            prediction = self.model.predict(X)[0]
            return round(prediction, 2)
        # fallback
        return current_patients * avg_service_time * 0.1

    def train_model(self):
        """
        Train a simple linear regression model to predict queue length.
        """
        print("🧠 Training Predictive Analytics model...")

        # Dummy data (patients, service_time) -> queue_length
        X = np.random.randint(1, 50, (100, 2))
        y = X[:, 0] * 0.8 + X[:, 1] * 2 + np.random.randn(100) * 3  # simulate wait time

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = LinearRegression()
        model.fit(X_train, y_train)
        score = model.score(X_test, y_test)

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(model, self.model_path)
        self.model = model

        print(f"✅ Predictive model trained successfully (R²: {score:.2f})")
        return score

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print("📦 Loaded Predictive Analytics model.")
        else:
            print("⚠️ No trained model found.")
