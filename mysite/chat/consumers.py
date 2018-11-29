from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
import json

from django.contrib.auth import get_user_model

from chat.models import Post, OpenedChat

User = get_user_model()


def get_first_post():
    return Post.objects.first()


@database_sync_to_async
def get_users_chat(first_user, second_user):
    return OpenedChat.get_users_chat(first_user, second_user)


@database_sync_to_async
def get_user_by_username(username):
    return User.objects.get(username=username)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()

        second_username = self.scope['url_route']['kwargs']['room_name']
        self.second_user = await get_user_by_username(second_username)
        self.room = await get_users_chat(self.scope['user'], self.second_user)

        self.room_name = self.room.room_name
        self.room_group_name = 'chat_%s' % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user = self.scope['user'].username
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': user
            }
        )
        await self.channel_layer.group_send(
            'notifications',
            {
                'type': 'notification_message',
                'message': {'user': user, 'message': message}
            }
        )

    async def chat_message(self, event):
        message = event['message']
        user = event['user']

        await self.send(text_data=json.dumps({
            'message': message,
            'user': user
        }))


class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.room_group_name = 'notifications'

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )


    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'notification_post',
                'message': message
            }
        )


    def notification_post(self, event):
        message = event['message']

        self.send(text_data=json.dumps({
            'post': message
        }))

    def notification_message(self, event):
        message = event['message']

        self.send(text_data=json.dumps({
            'message': message
        }))