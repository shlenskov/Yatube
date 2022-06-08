from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст',
        )
        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_authorized_client_exists_at_desired_location(self):
        """Страница доступна авторизованному пользователю."""
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_template_authorized_client_exists_at_desired_location(self):
        """Тест названия шаблона - пользователь авторизован."""
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_guest_client_exists_at_desired_location(self):
        """Страница доступна неавторизованному пользователю."""
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                if address == '/create/':
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                elif address == f'/posts/{self.post.id}/edit/':
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    self.assertTemplateUsed(response, template)

    def test_urls_guest_client_non_existent_template(self):
        """Проверка на несуществеющий адрес /no_page/ для пользователя."""
        response = self.guest_client.get('/no_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
