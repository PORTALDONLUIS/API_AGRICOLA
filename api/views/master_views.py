from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..services.master_service import MasterService

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def master_bootstrap(request):
    data = MasterService.bootstrap()
    return Response(data)
