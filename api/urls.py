from django.urls import path
from api.views.tic_views import identidad_tic, puente_tic

from api.services.master_service import bootstrap
from api.views.brix_batch_views import SyncBrixBatchView
from api.views.auth_views import login_view, refresh_view
from api.views.persona_views import (
    PersonaConsultarDniView,
    PersonaDetailView,
    PersonaJornalUpsertView,
    PersonaListCreateView,
    PersonaTipoListView,
)
from api.views.plantillas_views import (
    DownloadBrixMoscatelRegistrosView,
    DeleteRegistroByClientIdView,
    PlantillasAsignadasView,
    SyncRegistroView,
    UploadRegistroFotoView,
)

urlpatterns = [
    path('tic/identidad/', identidad_tic, name='tic_identidad'),
    path('tic/asignaciones/<str:recurso>/', puente_tic, name='tic_asignaciones'),
    path('tic/asignaciones/<str:recurso>/<path:ident>/', puente_tic, name='tic_asignaciones_detalle'),
    path('auth/login/', login_view, name='auth_login'),
    path("plantillas/asignadas/", PlantillasAsignadasView.as_view(), name="plantillas_asignadas"),

    path("auth/refresh/", refresh_view),

    path("registros/sync/", SyncRegistroView.as_view()),
    path("registros/sync-batch/", SyncBrixBatchView.as_view(), name="registros_sync_batch"),
    path("registros/brix-moscatel/descargar/", DownloadBrixMoscatelRegistrosView.as_view()),
    path("registros/by-client/<str:client_record_id>/", DeleteRegistroByClientIdView.as_view()),
    path("registros/<int:registro_id>/fotos/", UploadRegistroFotoView.as_view()),

    path("persona-tipos/", PersonaTipoListView.as_view(), name="persona_tipos"),
    path("personas/", PersonaListCreateView.as_view(), name="personas"),
    path("personas/consultar-dni/", PersonaConsultarDniView.as_view(), name="personas_consultar_dni"),
    path("personas/jornal/", PersonaJornalUpsertView.as_view(), name="personas_jornal"),
    path("personas/<int:persona_id>/", PersonaDetailView.as_view(), name="persona_detail"),

    path("bootstrap", bootstrap, name="master-bootstrap"),

]
