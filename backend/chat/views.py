import requests
from backend import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import render, redirect
from .models import Room, Message
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .serializers import RoomSerializer, RoomCreateSerializer, MessageSerializer, UserSerializer
from .permissions import IsAdminUserOrReadOnly

class LoginView(TokenObtainPairView):
    pass

class RoomListCreateView(generics.ListCreateAPIView):
    queryset = Room.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdminUserOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RoomCreateSerializer
        return RoomSerializer

    def perform_create(self, serializer):
        room = serializer.save()
        room.members.add(self.request.user)

class RoomJoinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        try:
            room = Room.objects.get(id=room_id)
            room.members.add(request.user)
            return Response({'detail': 'Joined room successfully.'})
        except Room.DoesNotExist:
            return Response({'detail': 'Room not found.'}, status=status.HTTP_404_NOT_FOUND)

class RoomLeaveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        try:
            room = Room.objects.get(id=room_id)
            room.members.remove(request.user)
            return Response({'detail': 'Left room successfully.'})
        except Room.DoesNotExist:
            return Response({'detail': 'Room not found.'}, status=status.HTTP_404_NOT_FOUND)

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        return Message.objects.filter(room_id=room_id, status='approved')

class MessageCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        content = request.data.get('content')
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response({'detail': 'Room not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user not in room.members.all():
            return Response({'detail': 'You are not a member of this room.'}, status=status.HTTP_403_FORBIDDEN)

        message = Message.objects.create(
            room=room,
            user=request.user,
            content=content,
            status='pending'
        )

        from .tasks import moderate_message
        moderate_message.delay(message.id)

        return Response({'detail': 'Message sent for moderation.'}, status=status.HTTP_201_CREATED)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        api_url = getattr(settings, 'API_URL', 'http://localhost:8000')

        try:
            response = requests.post(f'{api_url}/api/login/', json={
                'username': username,
                'password': password
            })
        except requests.exceptions.ConnectionError:
            return render(request, 'registration/login.html', {
                'error': 'Erro de conexão com o servidor.'
            })

        if response.status_code == 200:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user) 
            token_data = response.json()
            request.session['access_token'] = token_data['access']
            return redirect('dashboard')

        return render(request, 'registration/login.html', {'error': 'Login inválido'})

    return render(request, 'registration/login.html')


@login_required
def chat_room(request):
    access_token = request.session.get('access_token')
    return render(request, 'chat/room.html', {'access_token': access_token})

@login_required
def dashboard_view(request):
    access_token = request.session.get('access_token')
    rooms = Room.objects.all()
    is_admin = request.user.role == 'admin'

    return render(request, 'chat/dashboard.html', {
        'rooms': rooms,
        'is_admin': is_admin,
        'access_token': access_token
    })

def create_room_view(request):
    if request.user.role != 'admin':
        return redirect('dashboard')

    if request.method == 'POST':
        name = request.POST.get('name')
        is_private = request.POST.get('is_private') == 'on'
        room = Room.objects.create(name=name, is_private=is_private)
        room.members.add(request.user)
        return redirect('dashboard')
    
def chat_room_by_id(request, room_id):
    access_token = request.session.get('access_token')
    return render(request, 'chat/room.html', {
        'room_id': room_id,
        'access_token': access_token
    })

def logout_view(request):
    """
    View para processar o logout do usuário.
    Encerra a sessão do usuário e redireciona para a página de login.
    """
    username = request.user.username
    logout(request)

    messages.success(request, f"Logout realizado com sucesso! Até logo, {username}.")

    return redirect('/')
