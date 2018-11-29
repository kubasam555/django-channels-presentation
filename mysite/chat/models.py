from asgiref.sync import async_to_sync
from channels import layers
from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class Post(models.Model):
    title = models.CharField(max_length=256)
    description = models.CharField(max_length=1024)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f'{self.title}'


@receiver(post_save, sender=Post)
def send_notification(sender, **kwargs):
    instance = kwargs['instance']
    channel_layer = layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)('notifications', {'type': 'notification_post', 'message': {'user': instance.user.username, 'id': instance.pk}})


class OpenedChat(models.Model):
    first_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    second_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    room_name = models.CharField(max_length=128)

    def __str__(self):
        return f'{self.first_user} - {self.second_user}'

    @classmethod
    def get_users_chat(cls, first_user, second_user):
        instance = cls.objects.filter(
            Q(first_user=first_user, second_user=second_user) |
            Q(first_user=second_user, second_user=first_user)
        ).distinct().first()
        if not instance:
            instance = cls.objects.create(
                first_user=first_user,
                second_user=second_user,
                room_name=f'{first_user.username}-{second_user.username}')
        return instance