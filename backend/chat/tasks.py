from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import time

PALAVRAS_PROIBIDAS = ['palavrão', 'ofensa', 'xingamento']

@shared_task
def moderate_message(message_id):
    try:
        from .models import Message
        
        message = Message.objects.select_related('user', 'room').get(id=message_id)
        
        time.sleep(1.5)

        content_lower = message.content.lower()
        has_forbidden_word = any(palavra in content_lower for palavra in PALAVRAS_PROIBIDAS)
        
        if has_forbidden_word or "inapropriado" in content_lower:
            message.status = 'rejected'
        else:
            message.status = 'approved'
        
        message.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{message.room.id}",
            {
                "type": "chat_message",
                "message": {
                    "id": message.id,
                    "user": message.user.username,
                    "content": message.content,
                    "status": message.status,
                    "timestamp": message.created_at.isoformat() if hasattr(message, 'created_at') else None
                }
            }
        )

        return f'Message {message_id} moderated as {message.status}'

    except Exception as e:
        return f'Error moderating message {message_id}: {str(e)}'