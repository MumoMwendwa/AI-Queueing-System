import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime
import joblib
import os
from django.conf import settings

class AIQueueOptimizer:
    def __init__(self):
        self.model_path = os.path.join(settings.BASE_DIR, 'ai_models', 'wait_time_model.pkl')
        self.model = self.load_model()
    
    def load_model(self):
        """Load trained model or create new one"""
        if os.path.exists(self.model_path):
            return joblib.load(self.model_path)
        else:
            return self.train_new_model()
    
    def train_new_model(self):
        """Train a new wait time prediction model"""
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        # TODO: Load historical data and train
        return model
    
    def predict_wait_time(self, department_id, current_queue, time_of_day):
        """Predict wait time in minutes"""
        features = self.prepare_features(department_id, current_queue, time_of_day)
        prediction = self.model.predict([features])[0]
        return max(0, round(prediction))
    
    def prepare_features(self, department_id, queue_length, time_of_day):
        """Prepare features for model prediction"""
        hour = time_of_day.hour
        day_of_week = time_of_day.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        
        return [department_id, queue_length, hour, day_of_week, is_weekend]