import time
import random
from collections import deque
from models import EstadoSemaforo, Vehiculo, Ambulancia
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

def tarea_semaforo(id_sem, evento_inicio, evento_fin, cola_gui, modo, evento_ambulancia=None, evento_ambulancia_activa=None, direccion_ambulancia=None):
    """Proceso/Hilo que controla un semáforo específico"""
    estado = EstadoSemaforo.ROJO
    cola_vehiculos = deque()
    contador_vehiculos = 0
    
    # Probabilidades de tráfico asimétrico para hacerlo interesante
    probabilidad_llegada = PROBABILIDAD_LLEGADA_NORTE_SUR if id_sem in ['N', 'S'] else PROBABILIDAD_LLEGADA_ESTE_OESTE

    while True:
        # Verificar si hay ambulancia activa y si es para esta dirección
        if evento_ambulancia_activa and evento_ambulancia_activa.is_set():
            # Obtener dirección de la ambulancia
            if direccion_ambulancia:
                if hasattr(direccion_ambulancia, 'value'):  # Multiprocessing Value
                    dir_amb = direccion_ambulancia.value.decode() if isinstance(direccion_ambulancia.value, bytes) else direccion_ambulancia.value
                elif isinstance(direccion_ambulancia, dict):  # Dict para threads
                    if 'lock' in direccion_ambulancia:
                        with direccion_ambulancia['lock']:
                            dir_amb = direccion_ambulancia.get('value', 'N')
                    else:
                        dir_amb = direccion_ambulancia.get('value', 'N')
                else:
                    dir_amb = 'N'
                
                # Si la ambulancia viene por esta dirección, darle paso inmediato
                if dir_amb == id_sem:
                    # Poner todos los semáforos en rojo (excepto este)
                    estado = EstadoSemaforo.VERDE
                    actualizar_gui(cola_gui, id_sem, estado, len(cola_vehiculos))
                    
                    # Esperar a que la ambulancia pase
                    cola_gui.put(("AMBULANCIA_CRUZANDO", id_sem))
                    time.sleep(2.0)  # Tiempo para que la ambulancia cruce
                    
                    # Volver a rojo
                    estado = EstadoSemaforo.ROJO
                    actualizar_gui(cola_gui, id_sem, estado, len(cola_vehiculos))
                    
                    # Limpiar evento de ambulancia
                    if evento_ambulancia:
                        evento_ambulancia.clear()
                    if evento_ambulancia_activa:
                        evento_ambulancia_activa.clear()
                    
                    cola_gui.put(("AMBULANCIA_COMPLETADA", id_sem))
                    continue
                else:
                    # Si la ambulancia viene por otra dirección, mantener en rojo
                    estado = EstadoSemaforo.ROJO
                    actualizar_gui(cola_gui, id_sem, estado, len(cola_vehiculos))
                    time.sleep(0.1)
                    continue
        
        # Reportar estado actual (Rojo) y tamaño de cola
        actualizar_gui(cola_gui, id_sem, estado, len(cola_vehiculos))
        
        # Simular llegada de vehículos en ROJO
        if random.random() < probabilidad_llegada:
            contador_vehiculos += 1
            v = Vehiculo(f"{id_sem}-{contador_vehiculos}", id_sem)
            cola_vehiculos.append(v)
            actualizar_gui(cola_gui, id_sem, estado, len(cola_vehiculos))
        
        # Verificar si es mi turno (VERDE) - pero solo si no hay ambulancia
        if evento_inicio.is_set() and not (evento_ambulancia_activa and evento_ambulancia_activa.is_set()):
            evento_inicio.clear()
            
            # --- FASE VERDE ---
            estado = EstadoSemaforo.VERDE
            inicio_verde = time.time()
            
            while time.time() - inicio_verde < TIEMPO_VERDE:
                # Verificar si hay ambulancia durante el verde
                if evento_ambulancia_activa and evento_ambulancia_activa.is_set():
                    # Detener inmediatamente y poner en rojo
                    estado = EstadoSemaforo.ROJO
                    actualizar_gui(cola_gui, id_sem, estado, len(cola_vehiculos))
                    # Limpiar evento de inicio para que no se quede atascado
                    evento_inicio.clear()
                    break
                
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
            
            # Solo continuar con amarillo si no fue interrumpido por ambulancia
            if estado == EstadoSemaforo.VERDE and not (evento_ambulancia_activa and evento_ambulancia_activa.is_set()):
                # --- FASE AMARILLA ---
                estado = EstadoSemaforo.AMARILLO
                actualizar_gui(cola_gui, id_sem, estado, len(cola_vehiculos))
                time.sleep(TIEMPO_AMARILLO)
                
                # --- FASE ROJA Y FIN DE TURNO ---
                estado = EstadoSemaforo.ROJO
                actualizar_gui(cola_gui, id_sem, estado, len(cola_vehiculos))
                evento_fin.set() # Avisar al controlador

        time.sleep(0.1) # Pequeño sleep para no quemar CPU en el loop

def tarea_controlador(eventos_inicio, eventos_fin, cola_gui, evento_ambulancia=None, evento_ambulancia_activa=None, direccion_ambulancia=None, ciclos_max=10):
    """Controlador central: Semáforos simultáneos (N-S juntos, E-O juntos)"""
    ciclo = 0
    
    # Pequeña pausa inicial
    time.sleep(1)
    
    while ciclo < ciclos_max:
        # Verificar si hay ambulancia activa - si es así, pausar el ciclo
        if evento_ambulancia_activa and evento_ambulancia_activa.is_set():
            # Esperar a que la ambulancia termine
            while evento_ambulancia_activa.is_set():
                time.sleep(0.1)
            # Pequeña pausa después de la ambulancia
            time.sleep(0.5)
            continue
        
        cola_gui.put(("CICLO", ciclo + 1))
        
        # FASE 1: Activar N y S simultáneamente
        eventos_inicio['N'].set()  # Dar verde a N
        eventos_inicio['S'].set()  # Dar verde a S
        
        # Esperar a que ambos terminen (con verificación de ambulancia)
        while not (eventos_fin['N'].is_set() and eventos_fin['S'].is_set()):
            if evento_ambulancia_activa and evento_ambulancia_activa.is_set():
                # Si hay ambulancia, limpiar eventos y esperar
                eventos_inicio['N'].clear()
                eventos_inicio['S'].clear()
                break
            time.sleep(0.1)
        
        if eventos_fin['N'].is_set() and eventos_fin['S'].is_set():
            # Limpiar eventos
            eventos_fin['N'].clear()
            eventos_fin['S'].clear()
        
        # Verificar ambulancia antes de continuar
        if evento_ambulancia_activa and evento_ambulancia_activa.is_set():
            continue
        
        # FASE 2: Activar E y O simultáneamente
        eventos_inicio['E'].set()  # Dar verde a E
        eventos_inicio['O'].set()  # Dar verde a O
        
        # Esperar a que ambos terminen (con verificación de ambulancia)
        while not (eventos_fin['E'].is_set() and eventos_fin['O'].is_set()):
            if evento_ambulancia_activa and evento_ambulancia_activa.is_set():
                # Si hay ambulancia, limpiar eventos y esperar
                eventos_inicio['E'].clear()
                eventos_inicio['O'].clear()
                break
            time.sleep(0.1)
        
        if eventos_fin['E'].is_set() and eventos_fin['O'].is_set():
            # Limpiar eventos
            eventos_fin['E'].clear()
            eventos_fin['O'].clear()
            
        ciclo += 1
    
    cola_gui.put(("FIN", True))

