from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import QueueTicket, Notification


def _queue_update_message(instance):
    patient_name = instance.patient.user.get_full_name() or instance.patient.user.username
    return f"Queue ticket {instance.ticket_number} for {patient_name} is now {instance.status.replace('_', ' ')} in {instance.department.name}."


@receiver(pre_save, sender=QueueTicket)
def queue_ticket_before_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_status = None
        return

    instance._previous_status = (
        QueueTicket.objects.filter(pk=instance.pk)
        .values_list('status', flat=True)
        .first()
    )

@receiver(post_save, sender=QueueTicket)
def queue_ticket_updated(sender, instance, **kwargs):
    """Send WebSocket update when queue ticket changes"""
    channel_layer = get_channel_layer()
    created = kwargs.get('created', False)
    previous_status = getattr(instance, '_previous_status', None)
    status_changed = created or previous_status != instance.status

    if not status_changed:
        return

    message = _queue_update_message(instance)

    for user in User.objects.filter(is_staff=True):
        Notification.objects.create(recipient=user, message=message)

    if channel_layer:
        # Send update to general queue channel
        async_to_sync(channel_layer.group_send)(
            'queue_queue_updates',
            {
                'type': 'queue_update',
                'message': message,
            }
        )

        # Send update to department-specific channel
        async_to_sync(channel_layer.group_send)(
            f'department_{instance.department.id}',
            {
                'type': 'department_update',
                'message': message,
                'queue_data': {
                    'ticket_number': instance.ticket_number,
                    'patient_name': instance.patient.user.get_full_name() or instance.patient.user.username,
                    'status': instance.status,
                }
            }
        )

@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    """Send WebSocket update when new notification is created"""
    if created:
        channel_layer = get_channel_layer()

        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'user_{instance.recipient.id}',
                {
                    'type': 'user_notification',
                    'message': 'New notification',
                    'notification': {
                        'id': instance.id,
                        'recipient': instance.recipient.username,
                        'message': instance.message,
                        'created_at': instance.created_at.isoformat()
                    }
                }
            )