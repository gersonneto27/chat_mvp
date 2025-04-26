from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import (
    login_view,
    chat_room,
    LoginView,
    RoomListCreateView,
    RoomJoinView,
    RoomLeaveView,
    MessageListView,
    MessageCreateView,
    dashboard_view,
    create_room_view,
    chat_room_by_id,
    logout_view
)

urlpatterns = [
    path('api/login/', TokenObtainPairView.as_view(), name='api-login'),
    path('', login_view, name='login'),
    path('chat/', chat_room, name='chat_room'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('rooms/create/', create_room_view, name='create_room'),
    path('chat/<int:room_id>/', chat_room_by_id, name='chat_room_by_id'),

    # API Views
    path('login/', LoginView.as_view(), name='login'),
    path('rooms/', RoomListCreateView.as_view(), name='room-list-create'),
    path('rooms/<int:room_id>/join/', RoomJoinView.as_view(), name='room-join'),
    path('rooms/<int:room_id>/leave/', RoomLeaveView.as_view(), name='room-leave'),
    path('rooms/<int:room_id>/messages/', MessageListView.as_view(), name='message-list'),
    path('rooms/<int:room_id>/messages/send/', MessageCreateView.as_view(), name='message-create'),
]