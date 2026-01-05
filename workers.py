import time
import random
from collections import deque
from models import EstadoSemaforo, Vehiculo
from utils import actualizar_gui
from config import (
    PROBABILIDAD_LLEGADA_NORTE_SUR, 
    PROBABILIDAD_LLEGADA_ESTE_OESTE,
    TIEMPO_VERDE,
    TIEMPO_AMARILLO
)

# ==========================================
# WORKERS Y LÓGICA DE NEGOCIO
# ==========================================

def tarea_semaforo(id_sem, evento_inicio, evento_fin, cola_gui, modo):
    """Proceso/Hilo que controla un semáforo específico"""
    estado = EstadoSemaforo.ROJO
    cola_vehiculos = deque()
    contador_vehiculos = 0
    
    # Probabilidades de tráfico asimétrico para hacerlo interesante
    probabilidad_llegada = PROBABILIDAD_LLEGADA_NORTE_SUR if id_sem in ['N', 'S'] else PROBABILIDAD_LLEGADA_ESTE_OESTE

    while True:
        # Reportar estado actual (Rojo) y tamaño de cola
        actualizar_gui(cola_gui, id_sem, estado, len(cola_vehiculos))
        
        # Simular llegada de vehículos en ROJO
        if random.random() < probabilidad_llegada:
            contador_vehiculos += 1
            v = Vehiculo(f"{id_sem}-{contador_vehiculos}", id_sem)
            cola_vehiculos.append(v)
            actualizar_gui(cola_gui, id_sem, estado, len(cola_vehiculos))
        
        # Verificar si es mi turno (VERDE)
        if evento_inicio.is_set():
            evento_inicio.clear()
            
            # --- FASE VERDE ---
            estado = EstadoSemaforo.VERDE
            inicio_verde = time.time()
            
            while time.time() - inicio_verde < TIEMPO_VERDE:
                # Si hay autos, cruzarlos
                if cola_vehiculos:
                    v_cruza = cola_vehiculos.popleft()
                    espera = time.time() - v_cruza.tiempo_llegada
                    
                    # ENVIAR SEÑAL DE CRUCE VISUAL A LA GUI
                    cola_gui.put(("ANIMACION_CRUCE", id_sem))
                    cola_gui.put(("STATS", espera))
                    
                    actualizar_gui(cola_gui, id_sem, estado, len(cola_vehiculos))
                    time.sleep(0.3) # Tiempo que toma cruzar físicamente
                else:
                    time.sleep(0.1)
                
            # --- FASE AMARILLA ---
            estado = EstadoSemaforo.AMARILLO
            actualizar_gui(cola_gui, id_sem, estado, len(cola_vehiculos))
            time.sleep(TIEMPO_AMARILLO)
            
            # --- FASE ROJA Y FIN DE TURNO ---
            estado = EstadoSemaforo.ROJO
            actualizar_gui(cola_gui, id_sem, estado, len(cola_vehiculos))
            evento_fin.set() # Avisar al controlador

        time.sleep(0.1) # Pequeño sleep para no quemar CPU en el loop

def tarea_controlador(eventos_inicio, eventos_fin, cola_gui, ciclos_max=10):
    """Controlador central: Semáforos simultáneos (N-S juntos, E-O juntos)"""
    ciclo = 0
    
    # Pequeña pausa inicial
    time.sleep(1)
    
    while ciclo < ciclos_max:
        cola_gui.put(("CICLO", ciclo + 1))
        
        # FASE 1: Activar N y S simultáneamente
        eventos_inicio['N'].set()  # Dar verde a N
        eventos_inicio['S'].set()  # Dar verde a S
        
        # Esperar a que ambos terminen
        eventos_fin['N'].wait()
        eventos_fin['S'].wait()
        
        # Limpiar eventos
        eventos_fin['N'].clear()
        eventos_fin['S'].clear()
        
        # FASE 2: Activar E y O simultáneamente
        eventos_inicio['E'].set()  # Dar verde a E
        eventos_inicio['O'].set()  # Dar verde a O
        
        # Esperar a que ambos terminen
        eventos_fin['E'].wait()
        eventos_fin['O'].wait()
        
        # Limpiar eventos
        eventos_fin['E'].clear()
        eventos_fin['O'].clear()
            
        ciclo += 1
    
    cola_gui.put(("FIN", True))

