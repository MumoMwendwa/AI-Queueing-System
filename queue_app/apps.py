from django.apps import AppConfig

class QueueAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'queue_app'

    def ready(self):
        from . import signals  # noqa: F401
