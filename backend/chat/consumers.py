import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

            await self.add_user_to_room()

            messages = await self.get_room_messages()
            if messages:
                await self.send(text_data=json.dumps({
                    'type': 'history_messages',
                    'messages': messages
                }))

            await self.send_members_list()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_join',
                    'username': self.scope["user"].username
                }
            )

    async def disconnect(self, close_code):
        if not self.scope["user"].is_anonymous:

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'username': self.scope["user"].username
                }
            )

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            await self.remove_user_from_room()

            await self.send_members_list()

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if data['type'] == 'send_message':
            message = await self.save_message(data['content'])

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'user': self.scope["user"].username,
                        'content': message.content,
                        'status': 'pending',
                        'timestamp': message.created_at.isoformat() if hasattr(message, 'created_at') else None
                    }
                }
            )

            from .tasks import moderate_message
            moderate_message.delay(message.id)


    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'system_message',
            'message': f"{event['username']} entrou na sala"
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            'type': 'system_message',
            'message': f"{event['username']} saiu da sala"
        }))

    async def members_list(self, event):
        await self.send(text_data=json.dumps({
            'type': 'members_list',
            'members': event['members'],
        }))

    async def send_members_list(self):
        members = await self.get_members()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'members_list',
                'members': members,
            }
        )

    @database_sync_to_async
    def get_members(self):
        from .models import Room
        from .serializers import UserSerializer
        
        room = Room.objects.get(id=self.room_id)
        users = room.members.all()
        serializer = UserSerializer(users, many=True)
        return serializer.data

    @database_sync_to_async
    def get_room_messages(self):
        from .models import Room, Message
        from django.core.serializers.json import DjangoJSONEncoder
        import json

        room = Room.objects.get(id=self.room_id)
        messages = Message.objects.filter(
            room=room, 
            status='approved'
        ).order_by('-created_at')[:50]

        result = []
        for msg in reversed(list(messages)):
            result.append({
                'id': msg.id,
                'user': msg.user.username,
                'content': msg.content,
                'status': msg.status,
                'timestamp': msg.created_at.isoformat() if hasattr(msg, 'created_at') else None
            })
        
        return result

    @database_sync_to_async
    def add_user_to_room(self):
        from .models import Room
        
        room = Room.objects.get(id=self.room_id)
        room.members.add(self.scope["user"])

    @database_sync_to_async
    def remove_user_from_room(self):
        from .models import Room
        
        room = Room.objects.get(id=self.room_id)
        room.members.remove(self.scope["user"])
        
    @database_sync_to_async
    def save_message(self, content):
        from .models import Room, Message
        
        room = Room.objects.get(id=self.room_id)
        message = Message.objects.create(
            room=room,
            user=self.scope["user"],
            content=content,
            status='pending'
        )
        return message