from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from api.serializers.auth_serializers import LoginSerializer
from api.services.auth_service import AuthService

@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]

    print("LOGIN:", username)
    print("Passw:", password)

    try:
        result = AuthService().login(username, password)
    except Exception as e:
        print("AuthService EX:", repr(e))
        return Response({"error": "Error interno de autenticación"}, status=500)

    print("RESULT:", bool(result))

    if not result:
        return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

    return Response(result, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_view(request):
    refresh_token = request.data.get("refresh")

    if not refresh_token:
        return Response(
            {"error": "refresh requerido"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        refresh = RefreshToken(refresh_token)
        return Response({
            "access": str(refresh.access_token)
        })
    except Exception:
        return Response(
            {"error": "refresh inválido o expirado"},
            status=status.HTTP_401_UNAUTHORIZED
        )
