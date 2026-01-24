import json

class DebugLoginRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/api/auth/login/" or  request.path == "/api/plantillas/asignadas/":
            print("\n=== DEBUG LOGIN REQUEST ===")
            print("REMOTE_ADDR:", request.META.get("REMOTE_ADDR"))
            print("HOST HEADER:", request.META.get("HTTP_HOST"))
            print("CONTENT_TYPE:", request.META.get("CONTENT_TYPE"))
            print("AUTH HEADER:", request.META.get("HTTP_AUTHORIZATION"))

            # body raw (cuidado si es muy grande)
            try:
                raw = request.body.decode("utf-8", errors="ignore")
                print("RAW BODY:", raw[:500])
            except Exception as e:
                print("RAW BODY ERROR:", repr(e))

        response = self.get_response(request)

        if request.path == "/api/auth/login/" or request.path == "/api/plantillas/asignadas/":
            print("RESPONSE STATUS:", response.status_code)
            print("=== END DEBUG LOGIN ===\n")

        return response
