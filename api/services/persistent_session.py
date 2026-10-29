"""Sesión móvil persistente; el access token conserva su caducidad normal."""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken


class PersistentRefreshToken(RefreshToken):
    def check_exp(self, claim="exp", current_time=None):
        # Solo se omite el plazo para tokens firmados emitidos con esta política.
        if claim == "exp" and self.payload.get("persistent_session") is True and "exp" not in self.payload:
            return
        return super().check_exp(claim=claim, current_time=current_time)

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        token["persistent_session"] = True
        del token["exp"]
        return token

    @property
    def access_token(self):
        access = super().access_token
        access.payload.pop("persistent_session", None)
        return access


def renew_session(raw_token):
    token = PersistentRefreshToken(raw_token)
    # Comprueba existencia, usuario activo y política de autenticación vigente.
    user = JWTAuthentication().get_user(token)
    persistent = PersistentRefreshToken.for_user(user)
    return {"access": str(persistent.access_token), "refresh": str(persistent)}
