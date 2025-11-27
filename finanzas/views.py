# finanzas/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
import random
import json

class EstadoAFIPView(APIView):
    """
    Simula la verificación de estado del servidor de AFIP
    """
    def get(self, request):
        
        # Simulamos la conexión con AFIP.
        
        estado_servidor = {
            "estado": "ONLINE",
            "servidor_destino": "AFIP Web Service Facturación",
            "latencia": f"{random.randint(20, 100)}ms",
            "mensaje": "Conexión exitosa con el entorno de pruebas AFIP."
        }
        
        return Response(estado_servidor)

class CalcularMonotributoView(APIView):
    """
    El Semáforo del Monotributo: Calcula riesgo basado en ingresos
    """
    def post(self, request):
        # Datos recibidos del frontend (lo que el usuario facturó)
        try:
            data = request.data
            ingresos_anuales = float(data.get('ingresos', 0))
        except (TypeError, ValueError):
            return Response({"error": "Ingreso no válido."}, status=400)
            
        
        # Límite de la Categoría A (Ejemplo, para simular la lógica)
        LIMITE_CAT_A = 2100000 
        
        consumido_porcentaje = (ingresos_anuales / LIMITE_CAT_A) * 100
        
        if consumido_porcentaje <= 75:
            semáforo = "VERDE"
            mensaje = f"Estás en Categoría A y usaste {consumido_porcentaje:.2f}% de tu límite. ¡Excelente!"
        elif consumido_porcentaje > 75 and consumido_porcentaje <= 100:
            semáforo = "AMARILLO"
            mensaje = f"¡Cuidado! Estás cerca ({consumido_porcentaje:.2f}%) del límite. Evalúa recategorizarte."
        else:
            semáforo = "ROJO"
            mensaje = f"¡ALERTA FISCAL! Has superado el límite ({consumido_porcentaje:.2f}%). Debes recategorizarte o podrías ser excluido."

        return Response({
            "semáforo": semáforo,
            "mensaje": mensaje,
            "ingresos_evaluados": ingresos_anuales,
            "limite_categoria_A": LIMITE_CAT_A
        })
