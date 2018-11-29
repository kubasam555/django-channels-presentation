import json

from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DetailView

from chat.models import Post

User = get_user_model()


def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'index.html', {})


def chat(request):
    if not request.user.is_authenticated:
        return redirect('login')
    users = User.objects.exclude(pk=request.user.pk)
    return render(request, 'chat/chat_index.html', {'users': users})


def room(request, room_name):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'chat/room.html', {
        'room_name_json': mark_safe(json.dumps(room_name))
    })


class PostView(CreateView):
    model = Post
    fields = ['title', 'description']
    template_name = 'post_form.html'

    def post(self, request, *args, **kwargs):
        Post.objects.create(
            title=request.POST['title'],
            description=request.POST['description'],
            user=request.user
        )
        return redirect('index')


class PostDetail(DetailView):
    queryset = Post.objects.all()
    template_name = 'post_detail.html'
