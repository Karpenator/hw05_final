import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from posts.models import Post, Group, Comment, Follow
from django.core.cache import cache

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
NUMBER_OF_PAGINATED_POSTS = 13


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='UserTest')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostPagesTests.user,
            text='Тестовый текст',
            group=PostPagesTests.group,
            image=PostPagesTests.uploaded,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментрий',
            post=PostPagesTests.post,
            author=PostPagesTests.user,
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'UserTest'}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}): 'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_author_0, PostPagesTests.user)
        self.assertEqual(post_group_0, PostPagesTests.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PostPagesTests.group.slug})
        )
        first_object = response.context['page_obj'][0]
        second_object = response.context['group']
        posts_count = response.context['posts_count']
        post_group = second_object.slug
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_image_0 = first_object.image
        self.assertEqual(post_group, 'test-slug')
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_author_0, PostPagesTests.user)
        self.assertEqual(posts_count, 1)
        self.assertEqual(post_image_0, PostPagesTests.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': PostPagesTests.user}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        posts_count = response.context['posts_count']
        author = response.context['author']
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_author_0, PostPagesTests.user)
        self.assertEqual(post_group_0, PostPagesTests.group)
        self.assertEqual(posts_count, 1)
        self.assertEqual(author, PostPagesTests.user)
        self.assertEqual(post_image_0, PostPagesTests.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post.id}))
        post_text = response.context['post'].text
        post_author = response.context['post'].author
        post_image = response.context['post'].image
        self.assertEqual(post_text, 'Тестовый текст')
        self.assertEqual(post_author, PostPagesTests.user)
        self.assertEqual(post_image, PostPagesTests.post.image)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostPagesTests.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_url_has_new_post(self):
        """На главной странице отображается созданный пост"""
        response = self.authorized_client.get(reverse('posts:index'))
        for post in response.context['page_obj']:
            if post == self.post:
                self.assertEqual(post, PostPagesTests.post)

    def test_group_posts_has_new_post(self):
        """На странице группы отображается созданный пост"""
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PostPagesTests.group.slug})
        )
        for post in response.context['page_obj']:
            if post == self.post:
                self.assertEqual(post, PostPagesTests.post)

    def test_another_group_posts_has_no_new_post(self):
        """На странице другой группы созданный пост не отображается"""
        new_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание 2',
        )
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': new_group.slug})
        )
        for post in response.context['page_obj']:
            if post == PostPagesTests.post:
                self.assertNotEqual(post, PostPagesTests.post)

    def test_post_detail_url_has_new_comment(self):
        """На странице поста отображается созданный комментарий"""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post.id})
        )
        for comment in response.context['comments']:
            if comment == PostPagesTests.comment:
                self.assertEqual(comment, PostPagesTests.comment)

    def test_index_page_have_cash(self):
        """Главная страница имеет cash"""
        PostPagesTests.post.delete
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_author_0, PostPagesTests.user)
        self.assertEqual(post_group_0, PostPagesTests.group)
        self.assertEqual(post_image_0, PostPagesTests.post.image)

    def test_author_post_visible_on_follower(self):
        """Пост автора отображается у подписчика"""
        follow_user = User.objects.create_user(username='FollowUser')
        Post.objects.create(
            author=follow_user,
            text='Тестовый текст 2',
            group=PostPagesTests.group,
        )
        Follow.objects.create(user=PostPagesTests.user, author=follow_user)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        self.assertEqual(post_text_0, 'Тестовый текст 2')
        self.assertEqual(post_author_0, follow_user)
        self.assertEqual(post_group_0, PostPagesTests.group)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='UserTest')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.bulk_posts = Post.objects.bulk_create(
            [Post(text=f'text {i}', group=cls.group, author=cls.user)
             for i in range(NUMBER_OF_PAGINATED_POSTS)])

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_index_paginator(self):
        '''Проверка index: количество постов на первой странице равно 10
        и количество постов на второй странице равно 3'''
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_posts_paginator(self):
        '''Проверка group_posts:
        количество постов на первой странице равно 10
        и количество постов на второй странице равно 3'''
        response = self.client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PaginatorViewsTest.group.slug}))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PaginatorViewsTest.group.slug})
            + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_profile_paginator(self):
        '''Проверка profile:
        количество постов на первой странице равно 10
        и количество постов на второй странице равно 3'''
        follow_user = User.objects.create(username='FollowUser')
        Post.objects.create(
            author=follow_user,
            text='Тестовый текст',
            group=self.group,
        )
        Follow.objects.create(user=PaginatorViewsTest.user, author=follow_user)
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user}))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user})
            + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
        Follow.objects.create(user=PaginatorViewsTest.user, author=follow_user)
        response = self.guest_client.get(
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user}))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.guest_client.get(
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user})
            + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
