import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from hatchway.auth import SessionAuthBackend, TokenAuthBackend, authenticate_request
from hatchway.models import AuthToken


@pytest.mark.django_db
class TestAuthBackends:
    def test_session_auth_backend_authenticated_user(self):
        user = User.objects.create_user("testuser", "test@example.com", "password")
        factory = RequestFactory()
        request = factory.get("/")
        request.user = user

        backend = SessionAuthBackend()
        authenticated_user = backend.authenticate(request)

        assert authenticated_user == user

    def test_session_auth_backend_no_user(self):
        factory = RequestFactory()
        request = factory.get("/")
        # No user attribute

        backend = SessionAuthBackend()
        authenticated_user = backend.authenticate(request)

        assert authenticated_user is None

    def test_token_auth_backend_valid_token(self):
        user = User.objects.create_user("testuser", "test@example.com", "password")
        token = AuthToken.create_token(user, description="Test token")

        factory = RequestFactory()
        request = factory.get("/", HTTP_AUTHORIZATION=f"Token {token.key}")

        backend = TokenAuthBackend()
        authenticated_user = backend.authenticate(request)

        assert authenticated_user == user

    def test_token_auth_backend_invalid_token(self):
        factory = RequestFactory()
        request = factory.get("/", HTTP_AUTHORIZATION="Token invalid_token_123")

        backend = TokenAuthBackend()
        authenticated_user = backend.authenticate(request)

        assert authenticated_user is None

    def test_token_auth_backend_no_authorization_header(self):
        factory = RequestFactory()
        request = factory.get("/")

        backend = TokenAuthBackend()
        authenticated_user = backend.authenticate(request)

        assert authenticated_user is None

    def test_token_auth_backend_wrong_prefix(self):
        factory = RequestFactory()
        request = factory.get("/", HTTP_AUTHORIZATION="Bearer some_token")

        backend = TokenAuthBackend()
        authenticated_user = backend.authenticate(request)

        assert authenticated_user is None

    def test_authenticate_request_tries_backends_in_sequence(self):
        user = User.objects.create_user("testuser", "test@example.com", "password")
        token = AuthToken.create_token(user)

        factory = RequestFactory()
        # No session, but valid token
        request = factory.get("/", HTTP_AUTHORIZATION=f"Token {token.key}")

        authenticated_user, backend_name = authenticate_request(request)

        assert authenticated_user == user
        assert backend_name == "TokenAuthBackend"

    def test_authenticate_request_returns_none_when_all_fail(self):
        factory = RequestFactory()
        request = factory.get("/")

        authenticated_user, backend_name = authenticate_request(request)

        assert authenticated_user is None
        assert backend_name is None

    def test_authenticate_request_prefers_session(self):
        user = User.objects.create_user("testuser", "test@example.com", "password")
        token = AuthToken.create_token(user)

        factory = RequestFactory()
        request = factory.get("/", HTTP_AUTHORIZATION=f"Token {token.key}")
        request.user = user  # Session auth

        authenticated_user, backend_name = authenticate_request(request)

        assert authenticated_user == user
        assert backend_name == "SessionAuthBackend"  # Session tried first
