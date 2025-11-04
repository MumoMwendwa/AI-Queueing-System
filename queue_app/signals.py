from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import QueueTicket, Notification

@receiver(post_save, sender=QueueTicket)
def queue_ticket_updated(sender, instance, **kwargs):
    """Send WebSocket update when queue ticket changes"""
    channel_layer = get_channel_layer()
    
    # Send update to general queue channel
    async_to_sync(channel_layer.group_send)(
        'queue_queue_updates',
        {
            'type': 'queue_update',
            'message': f'Queue updated for {instance.department.name}'
        }
    )
    
    # Send update to department-specific channel
    async_to_sync(channel_layer.group_send)(
        f'department_{instance.department.id}',
        {
            'type': 'department_update',
            'message': 'Queue updated',
            'queue_data': {
                'ticket_number': instance.ticket_number,
                'patient_name': f"{instance.patient.first_name} {instance.patient.last_name}",
                'status': instance.status
            }
        }
    )

@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    """Send WebSocket update when new notification is created"""
    if created:
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f'doctor_{instance.doctor.id}',
            {
                'type': 'doctor_notification',
                'message': 'New notification',
                'notification': {
                    'id': instance.id,
                    'patient_name': f"{instance.patient.first_name} {instance.patient.last_name}",
                    'message': instance.message,
                    'created_at': instance.created_at.isoformat()
                }
            }
        )