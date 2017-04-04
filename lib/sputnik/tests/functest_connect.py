import json

from rest_framework import status

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User


class ConnectTest(TestCase):
    ERROR_MESSAGE = {'messages': [], 'result': False, 'status': False}
    EMPTY_MESSAGE = {'messages': [], 'result': True, 'status': True}

    def setUp(self):
        self.dispatcher = reverse('sputnik_dispatcher')
        user = User.objects.create_user('booktype', 'booktype@booktype.pro', 'password')

    def test_anon_get_connect(self):
        response = self.client.get(self.dispatcher)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.content, json.dumps(self.ERROR_MESSAGE))

    def test_get_connect(self):
        self.client.login(username='booktype', password='password')
        response = self.client.get(self.dispatcher, follow=True)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.content, json.dumps(self.ERROR_MESSAGE))

    def test_anon_post_connect(self):
        response = self.client.post(self.dispatcher)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.content, json.dumps(self.EMPTY_MESSAGE))

    def test_post_connect(self):
        self.client.login(username='booktype', password='password')
        response = self.client.post(self.dispatcher, follow=True)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.content, json.dumps(self.EMPTY_MESSAGE))

    def test_post_connect_garbage(self):
        self.client.login(username='booktype', password='password')
        response = self.client.post(self.dispatcher,
                                    {'clientID': None,
                                     'messages': None},
                                    follow=True)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.content, json.dumps(self.ERROR_MESSAGE))
