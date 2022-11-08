from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from InvoiceEngineApp.views.general_views import UserProfilePage


class ProfileTest(TestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='jacob', email='jacob@…', password='top_secret')

    def test_details(self):
        # Create an instance of a GET request.
        request = self.factory.get('/profile')

        request.user = self.user
        response = UserProfilePage.as_view()(request)
        self.assertEqual(response.status_code, 200)
