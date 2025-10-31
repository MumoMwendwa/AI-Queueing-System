import random

class PredictiveAnalytics:
    def __init__(self, data):
        self.data = data  # could be patient visit data, timestamps, etc.

    def predict_queue_length(self):
        """
        Dummy prediction — replace with trained model in future.
        """
        current_hour = self.data.get('hour', 12)
        if 9 <= current_hour <= 11:
            return random.randint(15, 25)  # peak hours
        elif 12 <= current_hour <= 15:
            return random.randint(5, 15)
        return random.randint(1, 10)

    def predict_wait_time(self):
        """
        Predict average waiting time (in minutes).
        """
        queue_length = self.predict_queue_length()
        return queue_length * 5  # assume avg 5 mins per patient

    def get_queue_message(self):
        """
        Return a message based on queue length.
        """
        queue_length = self.predict_queue_length()
        if queue_length >= 15:
            return f"High queue expected ({queue_length} patients)."
        elif 5 <= queue_length < 15:
            return f"Moderate queue expected ({queue_length} patients)."
        else:
            return f"Low queue expected ({queue_length} patients)."
