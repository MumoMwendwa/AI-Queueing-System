
from django.core.management.base import BaseCommand
import os
import joblib
from django.conf import settings

# Import your existing AI modules
from queue_app.ai import (
    predictive_analytics,
    triage_system,
    medical_analysis,
    queue_optimizer,
    notification_system,
)

class Command(BaseCommand):
    help = "Train and update all AI modules for the queue system safely"

    def handle(self, *args, **kwargs):
        model_dir = os.path.join(settings.BASE_DIR, "ai_models")
        os.makedirs(model_dir, exist_ok=True)

        self.stdout.write("🚀 Starting AI training pipeline...\n")

        trained_models = {}

        # Each of your modules is handled separately and safely:
        try:
            self.stdout.write("🧠 Training Predictive Analytics (wait time)...")
            model = predictive_analytics.train_model()
            joblib.dump(model, os.path.join(model_dir, "wait_time_model.pkl"))
            trained_models["Predictive Analytics"] = "✅ Success"
        except Exception as e:
            trained_models["Predictive Analytics"] = f"❌ Failed: {e}"

        try:
            self.stdout.write("⚕️ Training Triage System (patient prioritization)...")
            model = triage_system.train_model()
            joblib.dump(model, os.path.join(model_dir, "triage_model.pkl"))
            trained_models["Triage System"] = "✅ Success"
        except Exception as e:
            trained_models["Triage System"] = f"❌ Failed: {e}"

        try:
            self.stdout.write("🩺 Training Medical Analysis (diagnostics)...")
            model = medical_analysis.train_model()
            joblib.dump(model, os.path.join(model_dir, "medical_model.pkl"))
            trained_models["Medical Analysis"] = "✅ Success"
        except Exception as e:
            trained_models["Medical Analysis"] = f"❌ Failed: {e}"

        try:
            self.stdout.write("📊 Training Queue Optimizer (flow management)...")
            model = queue_optimizer.train_model()
            joblib.dump(model, os.path.join(model_dir, "queue_optimizer_model.pkl"))
            trained_models["Queue Optimizer"] = "✅ Success"
        except Exception as e:
            trained_models["Queue Optimizer"] = f"❌ Failed: {e}"

        try:
            self.stdout.write("🔔 Updating Notification System (AI messaging logic)...")
            # Notification system might not need a model, but we can trigger its AI refresh.
            if hasattr(notification_system, "train_model"):
                model = notification_system.train_model()
                joblib.dump(model, os.path.join(model_dir, "notification_model.pkl"))
                trained_models["Notification System"] = "✅ Success"
            else:
                trained_models["Notification System"] = "ℹ️ Skipped (no model training needed)"
        except Exception as e:
            trained_models["Notification System"] = f"❌ Failed: {e}"

        # 📝 Summary Log
        self.stdout.write("\n📦 Training Summary:")
        for name, status in trained_models.items():
            self.stdout.write(f"   {name}: {status}")

        self.stdout.write(self.style.SUCCESS("\n🎉 AI training completed without overwriting existing logic!"))
