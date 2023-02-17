from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Comment, Follow, Group, Post, User

POSTS_ON_SECOND_PAGE = 3
SUM_PAGES = settings.POSTS_ON_PAGE + POSTS_ON_SECOND_PAGE


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.bulk_create(Post(
            author=cls.user,
            group=cls.group,
            text=f'какой-то текст {i}')
            for i in range(SUM_PAGES)
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_contains_ten_records(self):
        """На страницу выводится 10 постов"""
        pages = [
            (reverse('posts:index'),
             settings.POSTS_ON_PAGE),
            (reverse('posts:group_list',
                     kwargs={'slug': self.group.slug}),
             settings.POSTS_ON_PAGE),
            (reverse('posts:profile',
                     kwargs={'username': self.user}),
             settings.POSTS_ON_PAGE),
            ((reverse('posts:index') + '?page=2'),
             POSTS_ON_SECOND_PAGE),
            ((reverse('posts:group_list',
                      kwargs={'slug': self.group.slug}) + '?page=2'),
             POSTS_ON_SECOND_PAGE),
            ((reverse('posts:profile',
                      kwargs={'username': self.user}) + '?page=2'),
             POSTS_ON_SECOND_PAGE),
        ]
        for reverse_name, posts in pages:
            with self.subTest(reverse_name=reverse_name, posts=posts):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), posts)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='NoName')
        cls.user2 = User.objects.create_user(username='SomeName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестова группа2',
            slug='test-slug2',
            description='Тестовое описание2'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.following_client = Client()
        self.following_client.force_login(self.user2)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}
                    ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def fields_to_check_in_context(self, post):
        """общая функция для проверки контекста"""
        fields = {
            post.pk: self.post.pk,
            post.author: self.user,
            post.group.title: self.group.title,
            post.text: self.post.text,
            post.image: self.post.image,
        }
        for field, expected in fields.items():
            with self.subTest(expected=expected):
                self.assertEqual(field, expected)

    def test_index_page_show_correct_context(self):
        """Главная страница отображает список постов."""
        response = self.authorized_client.get(reverse('posts:index'))
        expected_context = response.context['page_obj'][0]
        self.fields_to_check_in_context(expected_context)

    def test_group_list_show_correct_context(self):
        """Отображает список отфильтрованных по группе постов."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        expected_context = response.context['page_obj'][0]
        expected_group = response.context['group']
        self.fields_to_check_in_context(expected_context)
        self.assertEqual(expected_group, self.group)

    def test_profile_page_show_correct_context(self):
        """Отображает список отфильтрованных по автору постов."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        expected_context = response.context['page_obj'][0]
        expected_author = response.context['author']
        self.fields_to_check_in_context(expected_context)
        self.assertEqual(expected_author, self.user)

    def test_post_detail_show_correct_context(self):
        """Отображает один отфильтрованный по id пост."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        expected_context = response.context['post']
        self.fields_to_check_in_context(expected_context)

    def test_post_edit_show_correct_context(self):
        """Форма редактирования поста отфильтрованного по id."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Форма создания поста."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_new_post_not_in_wrong_group(self):
        """Проверка, что пост не попал в ненужную группу."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group2.slug}))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_comment_post_authorized_user(self):
        """Kомментировать посты может только авторизованный пользователь."""
        page = reverse('posts:add_comment', kwargs={'post_id': self.post.pk})
        response = self.authorized_client.get(page, follow=True)
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': self.post.pk}))

    def test_comment_show_on_page(self):
        """Rомментарий появляется на странице."""
        response_1 = self.authorized_client.get(reverse(
            'posts:post_detail', args=(self.post.pk,)
        ))
        comments_count = len(response_1.context['comments'])
        Comment.objects.create(
            post=self.post,
            text='тестовый коммент',
            author=self.user
        )
        response_2 = self.authorized_client.get(reverse(
            'posts:post_detail', args=(self.post.pk,)
        ))
        self.assertEqual(len(response_2.context['comments']),
                         comments_count + 1)

    def test_cache_index_page(self):
        """Главная страница кэшируется."""
        new_post = Post.objects.create(
            author=self.user,
            text='Новый тестовый пост',
            group=self.group,
        )
        response_1 = self.authorized_client.get(reverse('posts:index'))
        new_post.delete()
        response_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_2.content, response_1.content)
        cache.clear()
        response_3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_3.content, response_2.content)

    def test_user_can_follow_author(self):
        """Авторизованный пользователь может 
           подписываться и отписываться"""
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user2}))
        follow = Follow.objects.filter(user=self.user, author=self.user2)
        self.assertTrue(follow)
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user2}))
        unfollow = Follow.objects.filter(user=self.user,
                                         author=self.user2)
        self.assertFalse(unfollow)

    def test_followers_can_see_new_posts(self):
        """Пользователи видят новые посты в подписках"""
        Follow.objects.create(
            user=self.user,
            author=self.user2
        )
        Post.objects.create(
            text='Тестовый пост',
            author=self.user2
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(
            response.context['page_obj'][0].author,
            self.user2
        )
