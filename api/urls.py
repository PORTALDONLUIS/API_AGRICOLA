from django.urls import path

from api.views.auth_views import login_view, refresh_view
from api.views.plantillas_views import PlantillasAsignadasView

urlpatterns = [
    path('auth/login/', login_view, name='auth_login'),
    path("plantillas/asignadas/", PlantillasAsignadasView.as_view(), name="plantillas_asignadas"),

    path("api/auth/refresh/", refresh_view),

]