import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import QueueTicket, Department

class QueueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'queue_updates'
        self.room_group_name = f'queue_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'queue_update',
                'message': message
            }
        )

    # Receive message from room group
    async def queue_update(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'queue_data': await self.get_queue_data()
        }))

    @database_sync_to_async
    def get_queue_data(self):
        """Get current queue data for all departments"""
        departments = Department.objects.all()
        queue_data = {}
        
        for department in departments:
            waiting_count = QueueTicket.objects.filter(
                department=department,
                status='waiting'
            ).count()
            
            current_ticket = QueueTicket.objects.filter(
                department=department,
                status='in_consultation'
            ).first()
            
            queue_data[department.name] = {
                'waiting_count': waiting_count,
                'current_ticket': current_ticket.ticket_number if current_ticket else None,
                'current_patient': f"{current_ticket.patient.first_name} {current_ticket.patient.last_name}" if current_ticket else None
            }
        
        return queue_data

class DepartmentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.department_id = self.scope['url_route']['kwargs']['department_id']
        self.room_group_name = f'department_{self.department_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from room group
    async def department_update(self, event):
        message = event['message']
        queue_data = event['queue_data']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'queue_data': queue_data
        }))