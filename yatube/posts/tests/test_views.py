from http import HTTPStatus

from django import forms
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User
from ..utils import COUNT_POST

POST_PAGE_2 = 3
POST_ALL = COUNT_POST + POST_PAGE_2


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Neo')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст'
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        cls.templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts', args=(cls.group.slug,)
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', args=(cls.user.username,)
            ): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', args=(cls.post.id,)
            ): 'posts/create_post.html',
            reverse(
                'posts:post_detail', args=(cls.post.id,)
            ): 'posts/post_detail.html'
        }
        cls.comment = Comment.objects.create(
            text='Текст комментария',
            author=cls.user,
            post=cls.post
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_status_code(self):
        """Тест статусов"""
        for reverse_name, template in self.templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      args=(self.post.id,)))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def page_show_correct_context(self, response):
        """Шаблон index сформирован с правильным контекстом."""
        first_object = response.context['page_obj'][0]
        posts_text_0 = first_object.text
        posts_pub_date_0 = first_object.pub_date
        posts_author_0 = first_object.author.username
        posts_group_0 = first_object.group.title
        posts_image_0 = first_object.image
        self.assertEqual(posts_text_0, self.post.text)
        self.assertEqual(posts_pub_date_0, first_object.pub_date)
        self.assertEqual(posts_author_0, self.user.username)
        self.assertEqual(posts_group_0, self.group.title)
        self.assertEqual(posts_image_0, self.post.image)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.page_show_correct_context(response)

    def test_group_posts_pages_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', args=(self.group.slug,))
        )
        self.assertEqual(response.context['group'].title, self.group.title)
        self.assertEqual(response.context['group'].slug, self.group.slug)
        self.assertEqual(
            response.context['group'].description, self.group.description
        )
        self.page_show_correct_context(response)

    def test_profile_author_pages_show_correct_context(self):
        """Шаблон profile_author сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', args=(self.user.username,))
        )
        self.assertEqual(
            response.context['author'].username, self.user.username
        )
        self.page_show_correct_context(response)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        self.assertEqual(
            response.context['post'].author.username, self.user.username
        )
        self.assertEqual(response.context['post'].group.title,
                         self.group.title)
        self.assertEqual(response.context['post'].text, self.post.text)

    def test_post_create_correct_group(self):
        """Пост с указанной группой размещается корректно."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', args=(self.group.slug,))
        )
        posts_count = len(response.context['page_obj'])
        post_group = Group.objects.create(
            title='Тестовый заголовок 2',
            slug='test-slug-2',
            description='Описание-2'
        )
        Post.objects.create(
            author=self.user,
            group=self.group,
            text='Тестовый текст1',
        )
        response = self.authorized_client.get(
            reverse('posts:group_posts', args=(self.group.slug,))
        )
        self.assertEqual(len(response.context['page_obj']), posts_count + 1)
        response = self.authorized_client.get(
            reverse('posts:group_posts', args=(post_group.slug,))
        )
        self.assertFalse(len(response.context['page_obj']))

    def test_comment_on_post(self):
        """Комментарий появляется на странице поста."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        comments_count = len(response.context['comments'])
        Comment.objects.create(
            text='Текст комментария - 2',
            author=self.user,
            post=self.post
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        self.assertEqual(len(response.context['comments']), comments_count + 1)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Tanos')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Описание'
        )
        post_list = [
            Post(
                text=f"Тест {i}",
                author=cls.user,
                group=cls.group
            ) for i in range(POST_ALL)
        ]
        Post.objects.bulk_create(post_list)

    def test_first_page_contains_ten_records(self):
        templates_pages = {
            reverse('posts:index'): COUNT_POST,
            reverse(
                'posts:group_posts', args=(self.group.slug,)
            ): COUNT_POST,
            reverse(
                'posts:profile', args=(self.user.username,)
            ): COUNT_POST,
        }
        for reverse_name, value in templates_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), value)

    def test_second_page_contains_three_records(self):
        templates_pages = {
            reverse('posts:index'): POST_PAGE_2,
            reverse(
                'posts:group_posts', args=(self.group.slug,)
            ): POST_PAGE_2,
            reverse(
                'posts:profile', args=(self.user.username,)
            ): POST_PAGE_2,
        }
        for reverse_name, value in templates_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name, {'page': 2})
                self.assertEqual(len(response.context['page_obj']), value)


class PostCacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')

    def setUp(self):
        self.guest_client = Client()

    def test_index_cache(self):
        post = Post.objects.create(
            text='Тестовый пост',
            author=PostCacheTest.author,
        )
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 1)
        post.delete()
        response2 = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response2.content)
        cache.clear()
        response3 = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response3.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Forest')
        cls.author = User.objects.create_user(username='author')
        cls.nofollow = User.objects.create_user(username='follower')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст'
        )
        cls.follower = Follow.objects.create(
            author=cls.author,
            user=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user_client = Client()
        self.user_client.force_login(self.author)
        self.nofollow_client = Client()
        self.nofollow_client.force_login(self.nofollow)

    def test_authorized_client_following(self):
        """Авторизованный пользователь может подписываться на других
        пользователей"""
        response = self.nofollow_client.get(reverse('posts:follow_index'))
        count = len(response.context['page_obj'])
        self.assertFalse(count)
        self.nofollow_client.get(
            reverse('posts:profile_follow', args=(self.author,)))
        self.assertTrue(Follow.objects.filter(user=self.nofollow))

    def test_authorized_client_unfollowing(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан."""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        count = len(response.context['page_obj'])
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=(self.author,))
        )
        self.assertFalse(Follow.objects.filter(user=self.user))
        self.assertTrue(count)

    def test_post_on_list(self):
        """Пользователь видит посты автора на которого подписан"""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        count = len(response.context['page_obj'])
        Post.objects.create(
            author=self.author,
            text='Тестовый текст-2'
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), count + 1)

    def test_post_not_on_list(self):
        """Пользователь не видит посты автора на которого не подписан"""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertTrue(len(response.context['page_obj']))
        response = self.nofollow_client.get(reverse('posts:follow_index'))
        self.assertFalse(len(response.context['page_obj']))
