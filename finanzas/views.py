# finanzas/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import time

# Valores fijos de ejemplo para la simulación del semáforo
LIMITE_VERDE = 2000000 
LIMITE_AMARILLO = 2500000

class AfipEstado(APIView):
    """
    Simula el endpoint de prueba de conexión AFIP.
    """
    def get(self, request):
        time.sleep(0.02) # Simula latencia
        return Response({
            'estado': 'ÉXITO',
            'mensaje': 'Conexión exitosa con el entorno de pruebas AFIP.'
        }, status=status.HTTP_200_OK)


class MonotributoCalcular(APIView):
    """
    Calcula el estado del semáforo Monotributista.
    """
    def post(self, request):
        start_time = time.time()
        
        # 1. Obtener datos del Frontend (Vercel)
        cuit = request.data.get('cuit', 'N/A')
        ingresos = request.data.get('ingresos', 0)
        
        # Asegurarse de que ingresos es un número
        try:
            ingresos = float(ingresos)
        except ValueError:
            return Response({"error": "El valor de ingresos no es válido."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Lógica del Semáforo (Simulación basada en ingresos)
        if ingresos <= LIMITE_VERDE:
            semaforo = 'VERDE'
            mensaje = '¡Excelente! Sus ingresos están dentro de la categoría inicial de seguridad.'
        elif ingresos <= LIMITE_AMARILLO:
            semaforo = 'AMARILLO'
            mensaje = f'Advertencia: Sus ingresos de ${ingresos:,.2f} están cerca del límite. Considere recategorizar.'
        else:
            semaforo = 'ROJO'
            mensaje = f'¡Alerta! Sus ingresos de ${ingresos:,.2f} superan el límite de permanencia en el Régimen Simplificado (Monotributo).'
            
        end_time = time.time()
        latencia = int((end_time - start_time) * 1000)

        # 3. Respuesta al Frontend
        return Response({
            'semáforo': semaforo,
            'mensaje': mensaje,
            'latencia': latencia
        }, status=status.HTTP_200_OK)
