# core/urls.py
from django.contrib import admin
from django.urls import path
# Importamos las funciones del archivo views.py que acabamos de crear
from finanzas.views import EstadoAFIPView, CalcularMonotributoView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas API de TangoCash que causaban el 404
    path('api/v1/afip/estado/', EstadoAFIPView.as_view(), name='estado_afip'),
    path('api/v1/monotributo/calcular/', CalcularMonotributoView.as_view(), name='calcular_monotributo'),
]