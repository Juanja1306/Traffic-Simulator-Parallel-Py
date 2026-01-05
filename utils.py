import sys
import os
import threading
import multiprocessing
from config import MODO_ACTUAL, MODO_PROCESOS, MODO_HILOS

# ==========================================
# FUNCIONES UTILITARIAS
# ==========================================

def obtener_info_sistema(modo=None, workers=None):
    if modo is None:
        modo = MODO_ACTUAL
    
    # Contar hilos/procesos activos
    if modo == MODO_HILOS:
        # Usar workers si están disponibles (más confiable)
        if workers is not None:
            num_workers = len(workers)
        else:
            num_workers = threading.active_count() - 1  # -1 para excluir el main thread
        tipo_workers = "Hilos"
    else:
        # Usar workers si están disponibles (más confiable)
        if workers is not None:
            num_workers = len(workers)
        else:
            num_workers = len(multiprocessing.active_children())
        tipo_workers = "Procesos"
    
    info = {
        "python_ver": sys.version.split()[0],
        "os": sys.platform,
        "cpu_count": os.cpu_count(),
        "modo": modo,
        "num_workers": num_workers,
        "tipo_workers": tipo_workers
    }
    if hasattr(sys, "_is_gil_enabled"):
        info["gil_status"] = "Habilitado" if sys._is_gil_enabled() else "DESHABILITADO (Free-Threading)"
    else:
        info["gil_status"] = "Habilitado (Legacy)"
    return info

def actualizar_gui(cola, id_sem, estado, num_autos):
    cola.put(("UPDATE", id_sem, estado.value, num_autos))

