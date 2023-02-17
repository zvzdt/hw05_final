from http import HTTPStatus

from django.test import TestCase, Client
from django.core.cache import cache

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.not_author = User.objects.create_user(username='SomeName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)
        cache.clear()

    def test_page_matches_specific_client(self):
        """Общая проверка прав доступа клиентов к страницам."""
        match_check = [
            ('/', self.guest_client, HTTPStatus.OK),
            (f'/group/{self.group.slug}/', self.guest_client, HTTPStatus.OK),
            (f'/posts/{self.post.pk}/', self.guest_client, HTTPStatus.OK),
            ('/create/', self.authorized_client, HTTPStatus.FOUND),
            (f'/posts/{self.post.pk}/edit/',
             self.guest_client, HTTPStatus.FOUND),
            (f'/posts/{self.post.pk}/edit/',
             self.not_author_client, HTTPStatus.FOUND),
            (f'/posts/{self.post.pk}/edit/',
             self.authorized_client, HTTPStatus.FOUND),
            ('/unexisting_page/', self.guest_client.get, HTTPStatus.NOT_FOUND),
            (f'/profile/{self.user}/follow', self.guest_client.get,
             HTTPStatus.MOVED_PERMANENTLY),
        ]
        for address, client, response_code in match_check:
            with self.subTest(
                address=address,
                client=client,
                response_code=response_code
            ):
                response = self.client.get(address)
                self.assertEqual(response.status_code, response_code)

    def test_create_url_redirect_anonymous_on_login(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/', HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
