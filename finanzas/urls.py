# finanzas/urls.py
from django.urls import path
from .views import AfipEstado, MonotributoCalcular

urlpatterns = [
    # Endpoint de prueba para el estado general del servicio
    path('afip/estado/', AfipEstado.as_view(), name='afip-estado'),
    
    # Endpoint principal para el cálculo del semáforo
    path('monotributo/calcular/', MonotributoCalcular.as_view(), name='monotributo-calcular'),
]