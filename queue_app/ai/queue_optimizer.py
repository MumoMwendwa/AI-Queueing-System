# queue_app/ai/queue_optimizer.py
import joblib
import os
import numpy as np
from sklearn.cluster import KMeans

class QueueOptimizer:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), 'models', 'queue_optimizer.pkl')
        self.model = None

    def optimize_queue(self, queue_data):
        """
        Reorder patients based on priority clusters.
        """
        if not self.model:
            self.load_model()
        if not self.model:
            print("⚠️ No trained optimizer found. Returning original queue.")
            return queue_data

        X = np.array([[p['wait_time'], p['severity_score']] for p in queue_data])
        labels = self.model.predict(X)
        optimized = sorted(zip(labels, queue_data), key=lambda x: x[0])
        return [item[1] for item in optimized]

    def train_model(self):
        """
        Train a KMeans model to cluster patients by wait time & severity.
        """
        print("🧠 Training Queue Optimizer model...")

        X = np.random.randint(1, 100, (50, 2))  # [wait_time, severity_score]
        model = KMeans(n_clusters=3, random_state=42, n_init=10)
        model.fit(X)

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(model, self.model_path)
        self.model = model

        print("✅ Queue optimizer model trained successfully.")
        return True

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print("📦 Loaded Queue Optimizer model.")
        else:
            print("⚠️ No trained model found.")
