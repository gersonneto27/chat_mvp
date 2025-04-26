from django.test import TestCase

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import User, Room, Message

class ChatTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin', password='admin123', role='admin'
        )
        self.normal_user = User.objects.create_user(
            username='user', password='user123', role='normal'
        )

        self.client_admin = APIClient()
        response = self.client_admin.post(reverse('api-login'), {
            'username': 'admin',
            'password': 'admin123'
        }, format='json')
        self.admin_token = response.data['access']
        self.client_admin.credentials(HTTP_AUTHORIZATION='Bearer ' + self.admin_token)

        self.client_user = APIClient()
        response = self.client_user.post(reverse('api-login'), {
            'username': 'user',
            'password': 'user123'
        }, format='json')
        self.user_token = response.data['access']
        self.client_user.credentials(HTTP_AUTHORIZATION='Bearer ' + self.user_token)

    def test_admin_can_create_room(self):
        data = {'name': 'Sala de Teste'}
        response = self.client_admin.post(reverse('room-list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Room.objects.filter(name='Sala de Teste').exists())

    def test_normal_user_cannot_create_room(self):
        data = {'name': 'Sala Não Permitida'}
        response = self.client_user.post(reverse('room-list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_list_rooms(self):
        Room.objects.create(name='Sala Pública')
        response = self.client_user.get(reverse('room-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_send_message_to_room(self):
        room = Room.objects.create(name='Sala Mensagem')
        room.members.add(self.normal_user)

        data = {'content': 'Mensagem de Teste'}
        response = self.client_user.post(
            reverse('message-create', kwargs={'room_id': room.id}),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.filter(room=room).count(), 1)
        self.assertEqual(Message.objects.first().status, 'pending')

    def test_cannot_send_message_if_not_member(self):
        room = Room.objects.create(name='Sala Restrita')

        data = {'content': 'Tentativa de envio'}
        response = self.client_user.post(
            reverse('message-create', kwargs={'room_id': room.id}),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
