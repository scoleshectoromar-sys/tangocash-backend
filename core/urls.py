# core/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Conecta las URLs de la aplicación finanzas en el prefijo /api/v1/
    path('api/v1/', include('finanzas.urls')),
]