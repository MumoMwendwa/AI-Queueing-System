# queue_app/management/commands/train_ai_models.py

from django.core.management.base import BaseCommand
from sklearn.ensemble import RandomForestRegressor
import joblib
import os
from django.conf import settings
import numpy as np

class Command(BaseCommand):
    help = 'Train AI models used for the clinic queue system'

    def handle(self, *args, **kwargs):
        self.stdout.write("Training AI wait time prediction model...")

        # Example training data (replace later with real historical data)
        X = np.array([
            [1, 5, 10, 2, 0],   # [department_id, queue_length, hour, day_of_week, is_weekend]
            [1, 2, 15, 3, 0],
            [2, 8, 11, 5, 1],
            [3, 4, 9, 0, 0],
        ])
        y = np.array([20, 10, 30, 15])  # example wait times in minutes

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)

        # Save the model
        model_dir = os.path.join(settings.BASE_DIR, 'ai_models')
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, 'wait_time_model.pkl')
        joblib.dump(model, model_path)

        self.stdout.write(self.style.SUCCESS(f"✅ Model trained and saved to {model_path}"))
