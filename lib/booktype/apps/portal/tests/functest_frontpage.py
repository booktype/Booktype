from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User


class FrontpageTest(TestCase):
    def setUp(self):
        self.dispatcher = reverse('portal:frontpage')
        user = User.objects.create_user('booktype', 'booktype@booktype.pro', 'password')

    def test_frontpage(self):
        response = self.client.get(self.dispatcher)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['title'], 'Home')

