from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from users.forms import CreationForm
from http import HTTPStatus

User = get_user_model()


class UsersFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='UserTest')
        cls.form = CreationForm()

    def setUp(self):
        self.guest_client = Client()

    def test_create_user(self):
        '''Проверка signup: валидноcть формы и создание пользователя'''
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Petr',
            'last_name': 'Petrov',
            'username': 'Petr',
            'email': 'petr86@mail.ru',
            'password1': 'QWErty_123',
            'password2': 'QWErty_123',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            User.objects.count(), users_count + 1,
            'Новый пользователь не добавлен'
        )
