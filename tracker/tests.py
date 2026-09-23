from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from .models import JobApplication


class JobApplicationAPITests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", password="password")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        self.url = reverse("application-list")

    def test_create_application(self) -> None:
        """Ensure we can create a new job application object."""
        data = {
            "company_name": "Test Corp",
            "role": "Engineer",
            "status": JobApplication.Status.APPLIED,
            "applied_date": "2026-01-01",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(JobApplication.objects.count(), 1)
        self.assertEqual(JobApplication.objects.get().company_name, "Test Corp")

    def test_unauthenticated_request(self) -> None:
        """Ensure unauthenticated users get 401 Unauthorized."""
        self.client.credentials()  # Clear auth
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_scoping(self) -> None:
        """Ensure users can only see their own applications."""
        JobApplication.objects.create(
            user=self.user,
            company_name="User1 Corp",
            role="Dev",
            applied_date="2026-01-01",
        )

        user2 = User.objects.create_user(username="user2", password="password")
        JobApplication.objects.create(
            user=user2,
            company_name="User2 Corp",
            role="Dev",
            applied_date="2026-01-01",
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return the 1 application owned by the logged-in user
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["company_name"], "User1 Corp")
