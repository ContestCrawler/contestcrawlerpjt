from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from contests.models import Contest


class ContestCreateViewTests(TestCase):
    def test_get_create_page(self):
        response = self.client.get(reverse("contests:create"))

        self.assertEqual(response.status_code, 200)

    @patch("contests.views.build_prefill_data")
    def test_prefill_endpoint_renders_prefilled_form(self, mock_build_prefill_data):
        mock_build_prefill_data.return_value = {
            "source_url": "https://example.com/detail",
            "detail_url": "https://example.com/detail",
            "title": "Loaded title",
            "eligibility": "Anyone",
            "description": "Loaded description",
            "category": "idea",
            "host_region": "Seoul",
            "organizer": "OpenAI",
            "total_prize": "1000000",
            "first_prize": "500000",
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
            "content_type": "mixed",
            "image_urls": "https://example.com/image.jpg",
            "attachment_lines": "guide.pdf | https://example.com/guide.pdf",
            "is_active": True,
        }

        response = self.client.post(
            reverse("contests:prefill"),
            {"source_url": "https://example.com/detail"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"]["title"].value(), "Loaded title")
        mock_build_prefill_data.assert_called_once_with("https://example.com/detail")

    def test_create_post_saves_contest(self):
        response = self.client.post(
            reverse("contests:create"),
            {
                "title": "Spring Contest",
                "eligibility": "Anyone",
                "description": "Contest description",
                "category": "idea",
                "host_region": "Seoul",
                "organizer": "OpenAI",
                "total_prize": "1000000",
                "first_prize": "500000",
                "start_date": "2026-05-01",
                "end_date": "2026-05-31",
                "is_active": "on",
                "detail_url": "https://example.com/detail",
                "content_type": "mixed",
                "image_urls": "",
                "attachment_lines": "",
            },
        )

        self.assertRedirects(response, reverse("contests:create"))
        self.assertEqual(Contest.objects.count(), 1)
