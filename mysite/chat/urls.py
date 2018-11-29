from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('chat', views.chat, name='chat'),
    path('posts/add', views.PostView.as_view(), name='posts-add'),
    path('posts/<int:pk>', views.PostDetail.as_view(), name='posts-detail'),
    path('chat/<str:room_name>/', views.room, name='room'),
]
