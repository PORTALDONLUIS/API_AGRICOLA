from django.urls import path

from api.services.master_service import bootstrap
from api.views.auth_views import login_view, refresh_view
from api.views.plantillas_views import PlantillasAsignadasView, SyncRegistroView, UploadRegistroFotoView

urlpatterns = [
    path('auth/login/', login_view, name='auth_login'),
    path("plantillas/asignadas/", PlantillasAsignadasView.as_view(), name="plantillas_asignadas"),

    path("auth/refresh/", refresh_view),

    path("registros/sync/", SyncRegistroView.as_view()),
    path("registros/<int:registro_id>/fotos/", UploadRegistroFotoView.as_view()),

    path("bootstrap", bootstrap, name="master-bootstrap"),

]