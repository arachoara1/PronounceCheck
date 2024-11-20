from django.test import TestCase
from django.urls import reverse
from .models import User

class UserTestCase(TestCase):
    def test_user_creation(self):
        user = User(username='testuser', email='test@example.com')
        user.set_password('securepassword123')
        user.save()

        self.assertTrue(user.check_password('securepassword123'))

    def test_register_api(self):
        response = self.client.post(
            reverse('register'),
            data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'securepassword123'
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

    def test_login_api(self):
        user = User(username='testuser', email='test@example.com')
        user.set_password('securepassword123')
        user.save()

        response = self.client.post(
            reverse('login'),
            data={
                'username': 'testuser',
                'password': 'securepassword123'
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
