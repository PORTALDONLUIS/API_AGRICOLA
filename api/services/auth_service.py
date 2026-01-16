from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from api.repositories.portal_aei_repo import PortalAeiRepository

class AuthService:
    def __init__(self):
        self.repo = PortalAeiRepository()
        self.User = get_user_model()

    def login(self, username: str, password: str):
        portal_user = self.repo.validate_user(username, password)
        if not portal_user:
            return None

        # Obtener el user real (ya existe en dbo.user_user)
        user = self.User.objects.get(username=portal_user["username"])

        refresh = RefreshToken.for_user(user)

        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": f"{user.first_name} {user.last_name}".strip(),
                "email": user.email,
                "admin": getattr(user, "admin", False),
                "is_superuser": user.is_superuser,
                "dni": getattr(user, "dni", None),
            }
        }
