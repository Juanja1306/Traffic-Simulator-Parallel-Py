import tkinter as tk
import multiprocessing
import threading
import sys
from config import MODO_PROCESOS, MODO_HILOS, NUM_SEMAFOROS, NUM_CONTROLADORES, NUM_WORKERS_TOTAL
from workers import tarea_semaforo, tarea_controlador
from gui.app import TrafficApp

# ==========================================
# MAIN
# ==========================================

def seleccionar_modo():
    """Ventana de diálogo para seleccionar el modo de ejecución"""
    root = tk.Tk()
    root.title("Seleccionar Modo de Ejecución")
    root.geometry("400x200")
    root.resizable(False, False)
    
    # Centrar ventana
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (400 // 2)
    y = (root.winfo_screenheight() // 2) - (200 // 2)
    root.geometry(f"400x200+{x}+{y}")
    
    modo_seleccionado = [MODO_PROCESOS]  # Usar lista para modificar desde dentro de funciones
    
    # Frame principal
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Título
    titulo = tk.Label(frame, text="Seleccione el modo de ejecución:", 
                     font=("Arial", 12, "bold"))
    titulo.pack(pady=(0, 20))
    
    # Frame para botones
    frame_botones = tk.Frame(frame)
    frame_botones.pack(pady=10)
    
    # Botón Procesos
    btn_procesos = tk.Button(frame_botones, text="PROCESOS", 
                             font=("Arial", 11, "bold"),
                             width=15, height=2,
                             bg="#3498db", fg="white",
                             relief=tk.RAISED, bd=3,
                             command=lambda: [modo_seleccionado.__setitem__(0, MODO_PROCESOS), root.quit()])
    btn_procesos.pack(side=tk.LEFT, padx=10)
    
    # Botón Hilos
    btn_hilos = tk.Button(frame_botones, text="HILOS", 
                          font=("Arial", 11, "bold"),
                          width=15, height=2,
                          bg="#2ecc71", fg="white",
                          relief=tk.RAISED, bd=3,
                          command=lambda: [modo_seleccionado.__setitem__(0, MODO_HILOS), root.quit()])
    btn_hilos.pack(side=tk.LEFT, padx=10)
    
    # Información
    info = tk.Label(frame, text="Procesos: Mayor aislamiento\nHilos: Menor overhead", 
                   font=("Arial", 9), fg="#7f8c8d", justify=tk.LEFT)
    info.pack(pady=(10, 0))
    
    root.mainloop()
    root.destroy()
    
    return modo_seleccionado[0]

def main():
    # Configurar multiprocessing para Windows
    if sys.platform == 'win32':
        multiprocessing.set_start_method('spawn', force=True)
    
    # Mostrar diálogo de selección de modo
    modo_elegido = seleccionar_modo()
    
    # Selección de estrategia de concurrencia
    if modo_elegido == MODO_PROCESOS:
        cola_gui = multiprocessing.Queue()
        ManagerEvent = multiprocessing.Event
        WorkerClass = multiprocessing.Process
    else:
        import queue
        cola_gui = queue.Queue()
        ManagerEvent = threading.Event
        WorkerClass = threading.Thread

    eventos_inicio = {k: ManagerEvent() for k in ['N', 'S', 'E', 'O']}
    eventos_fin = {k: ManagerEvent() for k in ['N', 'S', 'E', 'O']}

    workers = []
    
    # Lanzar semáforos (NUM_SEMAFOROS workers)
    semaforos_ids = ['N', 'S', 'E', 'O']  # Debe coincidir con NUM_SEMAFOROS
    for sem_id in semaforos_ids:
        w = WorkerClass(target=tarea_semaforo, 
                        args=(sem_id, eventos_inicio[sem_id], eventos_fin[sem_id], cola_gui, modo_elegido))
        w.daemon = True
        w.start()
        workers.append(w)

    # Lanzar controlador (NUM_CONTROLADORES workers)
    for _ in range(NUM_CONTROLADORES):
        ctrl = WorkerClass(target=tarea_controlador, 
                           args=(eventos_inicio, eventos_fin, cola_gui))
        ctrl.daemon = True
        ctrl.start()
        workers.append(ctrl)
    
    # Total de workers: NUM_WORKERS_TOTAL (NUM_SEMAFOROS + NUM_CONTROLADORES)
    
    # Debug: Verificar que los workers se crearon correctamente
    print(f"\n{'='*60}")
    print(f"DEBUG: Workers creados en modo {modo_elegido}")
    print(f"{'='*60}")
    print(f"Total de workers: {len(workers)} (esperado: {NUM_WORKERS_TOTAL})")
    for i, w in enumerate(workers):
        estado = "Vivo" if w.is_alive() else "Muerto"
        if modo_elegido == MODO_HILOS:
            worker_id = w.ident if hasattr(w, 'ident') else "N/A"
            print(f"  Worker {i+1}: {w.name} (Thread ID: {worker_id}) - Estado: {estado}")
        else:
            worker_id = w.pid if hasattr(w, 'pid') and w.pid else "N/A"
            print(f"  Worker {i+1}: {w.name} (PID: {worker_id}) - Estado: {estado}")
    print(f"{'='*60}\n")

    # Pequeña pausa para que los workers se inicialicen antes de contar
    import time
    time.sleep(0.2)
    
    # Lanzar GUI (Main Thread)
    root = tk.Tk()
    app = TrafficApp(root, cola_gui, modo_elegido, workers)
    root.mainloop()

if __name__ == "__main__":
    main()

