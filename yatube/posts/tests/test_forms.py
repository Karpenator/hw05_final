import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from http import HTTPStatus
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='UserTest')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        '''Проверка post_create: валидноcть формы и создание поста'''
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'author': self.user,
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        if response.status_code == HTTPStatus.OK:
            self.assertRedirects(response, reverse(
                'posts:profile', kwargs={'username': self.user}))
            self.assertEqual(Post.objects.count(), posts_count + 1)
            self.assertTrue(
                Post.objects.filter(
                    text='Тестовый текст',
                    author=self.user,
                    image='posts/small.gif'
                ).exists())

    def test_post_edit(self):
        '''Проверка post_edit: валидноcть формы и изменение поста'''
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый текст',
            group=self.group
        )
        form_data = {
            'author': self.user,
            'text': 'Измененный текст'
        }
        original_post_text = self.post.text
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )        
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        if response.status_code == HTTPStatus.OK:
            self.post.refresh_from_db()
            changed_post_text = self.post.text
            self.assertNotEqual(
                changed_post_text, original_post_text, 'Пост не изменен')
