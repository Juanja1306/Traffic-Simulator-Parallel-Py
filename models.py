import time
from enum import Enum

# ==========================================
# MODELOS DE DATOS
# ==========================================

class EstadoSemaforo(Enum):
    ROJO = "red"
    AMARILLO = "yellow"
    VERDE = "green"

class Vehiculo:
    def __init__(self, id_vehiculo, direccion):
        self.id = id_vehiculo
        self.direccion = direccion 
        self.tiempo_llegada = time.time()

class Ambulancia(Vehiculo):
    """Vehículo de emergencia con prioridad absoluta"""
    def __init__(self, id_vehiculo, direccion):
        super().__init__(id_vehiculo, direccion)
        self.es_ambulancia = True
        self.prioridad = True

class Estadisticas:
    def __init__(self):
        self.total_vehiculos = 0
        self.tiempo_total_espera = 0.0
    
    def registrar_cruce(self, tiempo_espera):
        self.total_vehiculos += 1
        self.tiempo_total_espera += tiempo_espera

