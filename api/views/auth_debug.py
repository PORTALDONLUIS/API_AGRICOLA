from rest_framework_simplejwt.authentication import JWTAuthentication

class DebugJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            res = super().authenticate(request)  # (user, token) o None
            print("✅ JWT authenticate result:", res)
            return res
        except Exception as e:
            print("❌ JWT authenticate ERROR:", repr(e))
            raise
