from django.test import Client, TestCase
from django.contrib.auth.models import User
from django.conf import settings


class UserTestCase(TestCase):
    def setUp(self):
        username = '88888'
        password = 'Some_123'
        u = User(username=username)
        u.set_password(password)
        u.save()
        self.u = u
        self.assertEqual(u.username, username)
        self.assertTrue(u.check_password(password))

    def test_user_exists(self):
        user_count = User.objects.all().count()
        self.assertEqual(user_count, 1)  # ==
        self.assertNotEqual(user_count, 0)  # !=

    def test_login_url(self):
        login_url = "/login/"

        data = {"username": "88888", "password": "Some_123"}
        response = self.client.post(login_url, data, follow=True)
        status_code = response.status_code

        redirect_path = response.request.get("PATH_INFO")

        self.assertEqual(redirect_path, settings.LOGIN_REDIRECT_URL)
        self.assertEqual(status_code, 200)


class ClientTest(TestCase):
    def test_details(self):
        client = Client()
        res = client.get('/')
        self.assertEqual(res.status_code, 200)


"""         self.user = User.objects.create(
            first_name="johnContact",
            username="5588899",
            email="johnContact@example.com",
            role="ADMIN",
        )
        self.user.set_password("password")
        self.user.save() """
