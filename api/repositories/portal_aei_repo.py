from django.contrib.auth.hashers import check_password
from django.db import connections

class PortalAeiRepository:
    def validate_user(self, username: str, password: str):
        with connections["PORTAL_AEI"].cursor() as cursor:
            cursor.execute("""
                SELECT TOP 1
                    id,
                    username,
                    first_name,
                    last_name,
                    email,
                    password,
                    active,
                    is_superuser,
                    admin,
                    dni
                FROM dbo.user_user
                WHERE username = %s
            """, [username])

            row = cursor.fetchone()

        if not row:
            return None

        (user_id, usuario, first_name, last_name, email,
         password_hash, active, is_superuser, admin, dni) = row

        if not active:
            return None

        # ✅ valida pbkdf2_sha256$...
        if not check_password(password, password_hash):
            return None

        return {
            "id": user_id,
            "username": usuario,
            "first_name": first_name or "",
            "last_name": last_name or "",
            "email": email or "",
            "is_superuser": bool(is_superuser),
            "admin": bool(admin),
            "dni": dni,
        }
