from django.urls import path

from api.views.auth_views import login_view

urlpatterns = [
    path('auth/login/', login_view, name='auth_login'),
]