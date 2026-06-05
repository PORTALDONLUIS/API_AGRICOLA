from django.urls import path

from api.services.master_service import bootstrap
from api.views.auth_views import login_view, refresh_view
from api.views.persona_views import (
    PersonaConsultarDniView,
    PersonaDetailView,
    PersonaJornalUpsertView,
    PersonaListCreateView,
    PersonaTipoListView,
)
from api.views.plantillas_views import (
    DeleteRegistroByClientIdView,
    PlantillasAsignadasView,
    SyncRegistroView,
    UploadRegistroFotoView,
)

urlpatterns = [
    path('auth/login/', login_view, name='auth_login'),
    path("plantillas/asignadas/", PlantillasAsignadasView.as_view(), name="plantillas_asignadas"),

    path("auth/refresh/", refresh_view),

    path("registros/sync/", SyncRegistroView.as_view()),
    path("registros/by-client/<str:client_record_id>/", DeleteRegistroByClientIdView.as_view()),
    path("registros/<int:registro_id>/fotos/", UploadRegistroFotoView.as_view()),

    path("persona-tipos/", PersonaTipoListView.as_view(), name="persona_tipos"),
    path("personas/", PersonaListCreateView.as_view(), name="personas"),
    path("personas/consultar-dni/", PersonaConsultarDniView.as_view(), name="personas_consultar_dni"),
    path("personas/jornal/", PersonaJornalUpsertView.as_view(), name="personas_jornal"),
    path("personas/<int:persona_id>/", PersonaDetailView.as_view(), name="persona_detail"),

    path("bootstrap", bootstrap, name="master-bootstrap"),

]
