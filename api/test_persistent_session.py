import unittest
from types import SimpleNamespace
from unittest.mock import patch
from django.conf import settings
if not settings.configured:
    settings.configure(SECRET_KEY="session-tests-only-" * 4, INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes"], USE_TZ=True, SIMPLE_JWT={"AUTH_HEADER_TYPES": ("Bearer",)})
    import django
    django.setup()
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.exceptions import AuthenticationFailed
from api.services.persistent_session import PersistentRefreshToken, renew_session


class PersistentSessionTests(unittest.TestCase):
    def setUp(self):
        self.user = SimpleNamespace(id=7, is_active=True, password="test-hash")

    def test_refresh_has_no_expiry_but_access_expires(self):
        token = PersistentRefreshToken.for_user(self.user)
        self.assertNotIn("exp", token.payload)
        self.assertIn("exp", token.access_token.payload)
        self.assertNotIn("persistent_session", token.access_token.payload)
        PersistentRefreshToken(str(token))

    def test_old_persistent_session_renews(self):
        token = PersistentRefreshToken.for_user(self.user)
        token["iat"] = 946684800  # Año 2000; no depende del tiempo transcurrido.
        with patch("django.contrib.auth.models.User.objects.get", return_value=self.user):
            result = renew_session(str(token))
        self.assertEqual(str(AccessToken(result["access"])["user_id"]), "7")
        self.assertNotIn("exp", PersistentRefreshToken(result["refresh"]).payload)

    def test_valid_legacy_refresh_migrates(self):
        token = RefreshToken.for_user(self.user)
        with patch("django.contrib.auth.models.User.objects.get", return_value=self.user):
            result = renew_session(str(token))
        self.assertTrue(PersistentRefreshToken(result["refresh"])["persistent_session"])

    def test_expired_legacy_token_is_not_resurrected(self):
        token = RefreshToken.for_user(self.user)
        token["exp"] = 1
        with self.assertRaises(TokenError):
            renew_session(str(token))

    def test_tampered_signature_rejected(self):
        token = str(PersistentRefreshToken.for_user(self.user))
        parts = token.split(".")
        parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
        with self.assertRaises(TokenError):
            renew_session(".".join(parts))

    def test_access_cannot_be_used_as_refresh(self):
        with self.assertRaises(TokenError):
            renew_session(str(PersistentRefreshToken.for_user(self.user).access_token))

    def test_inactive_user_rejected(self):
        token = PersistentRefreshToken.for_user(self.user)
        self.user.is_active = False
        with patch("django.contrib.auth.models.User.objects.get", return_value=self.user):
            with self.assertRaises(AuthenticationFailed):
                renew_session(str(token))

