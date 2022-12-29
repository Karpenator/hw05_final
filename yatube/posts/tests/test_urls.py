from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group, Comment, Follow
from http import HTTPStatus
from django.urls import reverse

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostURLTests(TestCase):
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
            author=cls.user,
            text='Тестовый текст',
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментрий',
            post=cls.post,
            author=cls.user,
        )
        cls.templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/UserTest/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            '/posts/1/edit/': 'posts/post_create.html',
        }

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, templates in PostURLTests.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, templates)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='UserTest')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user_new = User.objects.create_user(username='User_not_author')

    def test_unexisting_page_authorized(self):
        """Страница /unexisting_page/ не существует"""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_guest_not_create_post(self):
        """Страница create недоступна неавторизованному пользователю
        и перенаправляет его на страницу авторизации"""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_guest_not_edit_post(self):
        """Страница post_edit недоступна неавторизованному
        пользователю и перенаправляет его на страницу авторизации"""
        response = self.guest_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostURLTests.post.id}),
            follow=True)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{ PostURLTests.post.id}/edit/')

    def test_not_author_not_edit_post(self):
        """ Не автор не может редактировать пост"""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_new)
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostURLTests.post.id}),
            follow=True)
        self.assertRedirects(
            response, f'/posts/{ PostURLTests.post.id}/')

    def test_index_url_desired_location(self):
        """Страница index доступна любому пользователю"""
        response = self.authorized_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_url_available_auth_user(self):
        """Страница profile доступна авторизованному пользователю"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_available_auth_user(self):
        """Страница create доступна авторизованному пользователю"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_available_auth_user(self):
        """Страница post_edit доступна авторизованному пользователю"""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostURLTests.post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_posts_url_available_auth_user(self):
        """Страница group_posts доступна авторизованному пользователю"""
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PostURLTests.post.id})
        )
        self.assertEqual(response.status_code, 404)

    def test_post_detail_available_auth_user(self):
        """Страница post_detail доступна авторизованному пользователю"""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostURLTests.post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_comment_available_auth_user(self):
        """Комментарии доступны авторизованному пользователю"""
        response = self.authorized_client.get(
            reverse('posts:add_comment',
                    kwargs={'post_id': PostURLTests.post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_404_page_uses_correct_template(self):
        """Страница 404 использует соответствующий шаблон."""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_auth_user_make_follow(self):
        """Авторизованный пользователь может подписываться на других"""
        follow_user = User.objects.create(username='FollowUser')
        response = self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': follow_user})
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_auth_user_make_unfollow(self):
        """Авторизованный пользователь может отписаться от других"""
        follow_user = User.objects.create(username='FollowUser')
        Follow.objects.create(user=self.user, author=follow_user)
        response = self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': follow_user})
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
