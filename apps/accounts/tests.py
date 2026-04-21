import shutil
import tempfile
from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Author, Education, User, UserCertificate, UserEducation, UserExperience, Wallet
from apps.common.models import Media
from apps.courses.models import Category, Course
from apps.notifications.models import Notification
from apps.payments.choices import CurrencyEnum


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "accounts-tests",
        }
    }
)
class RegistrationFlowTests(APITestCase):
    register_url = "/api/v1/accounts/register/"
    confirm_url = "/api/v1/accounts/register/confirm/"

    def tearDown(self):
        cache.clear()

    @patch("apps.accounts.views.auth.send_sms_to_phone_task.delay")
    def test_register_for_deleted_user_creates_new_user_and_keeps_deleted_record(self, mocked_sms_delay):
        deleted_user = User.objects.create_user(
            phone="+998901111111",
            password="old_password",
            is_active=False,
            is_deleted=True,
        )

        response = self.client.post(
            self.register_url,
            data={"phone": "+998901111111", "password": "new_password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        deleted_user.refresh_from_db()
        self.assertNotEqual(deleted_user.phone, "+998901111111")
        self.assertTrue(deleted_user.is_deleted)
        self.assertFalse(deleted_user.is_active)

        replacement_user = User.objects.get(phone="+998901111111")
        self.assertNotEqual(replacement_user.pk, deleted_user.pk)
        self.assertFalse(replacement_user.is_active)
        self.assertFalse(replacement_user.is_deleted)
        mocked_sms_delay.assert_called_once()
        self.assertIsNotNone(cache.get("sms_code:+998901111111"))

    @patch("apps.accounts.views.auth.send_sms_to_phone_task.delay")
    def test_register_for_existing_inactive_user_resends_sms_and_updates_password(self, mocked_sms_delay):
        user = User.objects.create_user(
            phone="+998902222222",
            password="old_password",
            is_active=False,
            is_deleted=False,
        )

        response = self.client.post(
            self.register_url,
            data={"phone": "+998902222222", "password": "new_password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("new_password"))
        self.assertFalse(user.is_active)
        self.assertEqual(User.objects.filter(phone="+998902222222").count(), 1)
        mocked_sms_delay.assert_called_once()
        self.assertIsNotNone(cache.get("sms_code:+998902222222"))

    @patch("apps.accounts.views.auth.send_sms_to_phone_task.delay")
    def test_register_confirm_creates_wallet_bonus_and_notification_once(self, mocked_sms_delay):
        register_response = self.client.post(
            self.register_url,
            data={"phone": "+998903333333", "password": "new_password"},
            format="json",
        )
        self.assertEqual(register_response.status_code, status.HTTP_200_OK)
        mocked_sms_delay.assert_called_once()
        code = cache.get("sms_code:+998903333333")
        self.assertIsNotNone(code)

        first_confirm = self.client.post(
            self.confirm_url,
            data={"phone": "+998903333333", "code": code},
            format="json",
        )
        self.assertEqual(first_confirm.status_code, status.HTTP_200_OK)

        user = User.objects.get(phone="+998903333333")
        user.refresh_from_db()
        self.assertTrue(user.is_active)

        wallet = Wallet.objects.get(user=user)
        self.assertEqual(wallet.balance, Decimal("10000"))
        self.assertEqual(Notification.objects.filter(user=user, title="Welcome").count(), 1)

        second_confirm = self.client.post(
            self.confirm_url,
            data={"phone": "+998903333333", "code": code},
            format="json",
        )
        self.assertEqual(second_confirm.status_code, status.HTTP_400_BAD_REQUEST)
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal("10000"))
        self.assertEqual(Wallet.objects.filter(user=user).count(), 1)
        self.assertEqual(Notification.objects.filter(user=user, title="Welcome").count(), 1)


class ProfileEditingFlowTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_root = tempfile.mkdtemp(prefix="uicdev-test-media-")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.settings_ctx = override_settings(MEDIA_ROOT=self._media_root)
        self.settings_ctx.enable()

        self.user = User.objects.create_user(phone="+998905555551", password="password", is_active=True)
        self.other_user = User.objects.create_user(phone="+998905555552", password="password", is_active=True)
        self.client.force_authenticate(user=self.user)

        self.education = Education.objects.create(name="MIT", type="University")
        author = Author.objects.create(first_name="Course", last_name="Author")
        category = Category.objects.create(name="Category")
        self.course = Course.objects.create(
            author=author,
            category=category,
            name="Course for certificate",
            price=10000,
            currency=CurrencyEnum.UZS,
            is_active=True,
            is_published=True,
        )

    def tearDown(self):
        self.settings_ctx.disable()

    def _create_media(self, file_name="cert.pdf", content=b"dummy-content"):
        upload = SimpleUploadedFile(file_name, content)
        return Media.objects.create(file=upload)

    def test_profile_patch_updates_user_main_fields(self):
        response = self.client.patch(
            "/api/v1/profile/",
            data={
                "first_name": "John",
                "last_name": "Doe",
                "bio": "Backend engineer",
                "age": 27,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Doe")
        self.assertEqual(self.user.bio, "Backend engineer")
        self.assertEqual(self.user.age, 27)

    def test_user_education_crud_with_validation_and_ownership(self):
        create_response = self.client.post(
            "/api/v1/profile/educations/",
            data={
                "education": self.education.id,
                "start_date": "2020-01-01",
                "end_date": "2024-01-01",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        created_id = create_response.data["id"]

        invalid_response = self.client.post(
            "/api/v1/profile/educations/",
            data={
                "education": self.education.id,
                "start_date": "2023-01-01",
                "end_date": "2022-12-31",
            },
            format="json",
        )
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_date", invalid_response.data)

        update_response = self.client.patch(
            f"/api/v1/profile/educations/{created_id}/",
            data={"end_date": "2025-02-01"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(UserEducation.objects.get(pk=created_id).end_date.isoformat(), "2025-02-01")

        other_item = UserEducation.objects.create(
            user=self.other_user,
            education=self.education,
            start_date="2022-01-01",
        )
        forbidden_response = self.client.patch(
            f"/api/v1/profile/educations/{other_item.id}/",
            data={"end_date": "2022-12-31"},
            format="json",
        )
        self.assertEqual(forbidden_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_experience_crud_with_validation(self):
        create_response = self.client.post(
            "/api/v1/profile/experiences/",
            data={
                "name": "UIC",
                "position": "Backend Developer",
                "start_date": "2021-01-01",
                "end_date": "2023-01-01",
                "website_url": "https://example.com",
                "skills": "django,postgres",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        created_id = create_response.data["id"]

        invalid_response = self.client.patch(
            f"/api/v1/profile/experiences/{created_id}/",
            data={"start_date": "2025-01-01", "end_date": "2024-01-01"},
            format="json",
        )
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_date", invalid_response.data)

        delete_response = self.client.delete(f"/api/v1/profile/experiences/{created_id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserExperience.objects.filter(pk=created_id).exists())

    def test_user_certificate_validates_attachment_and_supports_replace_delete(self):
        valid_attachment = self._create_media(file_name="cert.pdf")
        create_response = self.client.post(
            "/api/v1/profile/certificates/",
            data={
                "course": self.course.id,
                "name": "Python Certificate",
                "attachment": valid_attachment.id,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        cert_id = create_response.data["id"]

        invalid_ext_attachment = self._create_media(file_name="cert.exe")
        invalid_ext_response = self.client.post(
            "/api/v1/profile/certificates/",
            data={
                "course": self.course.id,
                "name": "Invalid Certificate",
                "attachment": invalid_ext_attachment.id,
            },
            format="json",
        )
        self.assertEqual(invalid_ext_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("attachment", invalid_ext_response.data)

        huge_attachment = self._create_media(file_name="huge.pdf", content=b"a" * (10 * 1024 * 1024 + 1))
        huge_response = self.client.post(
            "/api/v1/profile/certificates/",
            data={
                "course": self.course.id,
                "name": "Huge Certificate",
                "attachment": huge_attachment.id,
            },
            format="json",
        )
        self.assertEqual(huge_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("attachment", huge_response.data)

        replacement_attachment = self._create_media(file_name="replacement.jpg")
        replace_response = self.client.patch(
            f"/api/v1/profile/certificates/{cert_id}/",
            data={"attachment": replacement_attachment.id},
            format="json",
        )
        self.assertEqual(replace_response.status_code, status.HTTP_200_OK)

        certificate = UserCertificate.objects.get(pk=cert_id)
        self.assertEqual(certificate.attachment_id, replacement_attachment.id)

        delete_response = self.client.delete(f"/api/v1/profile/certificates/{cert_id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserCertificate.objects.filter(pk=cert_id).exists())
