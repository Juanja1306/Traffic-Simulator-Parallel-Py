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
    
    modo_seleccionado = [None]  # Usar lista para modificar desde dentro de funciones
    
    # Configurar ventana
    ancho_vent = 550
    alto_vent = 380
    
    # Centrar ventana
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cord = int((screen_width/2) - (ancho_vent/2))
    y_cord = int((screen_height/2) - (alto_vent/2))
    
    root.geometry(f"{ancho_vent}x{alto_vent}+{x_cord}+{y_cord}")
    root.resizable(False, False) # Tamaño fijo para mantener diseño
    
    # Paleta Cyber-Traffic (Sincronizada con config.py)
    bg_color = "#0f172a"      # Fondo principal
    card_bg = "#1e293b"       # Fondo secundario
    text_main = "#f1f5f9"     # Texto principal
    text_sec = "#94a3b8"      # Texto secundario
    accent_blue = "#3b82f6"   # Azul vibrante (Procesos)
    accent_green = "#10b981"  # Verde vibrante (Hilos)
    
    root.configure(bg=bg_color)
    root.title("Traffic Simulator Launcher")
    
    # Manejar cierre de ventana
    def on_closing():
        modo_seleccionado[0] = None
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Container principal con padding
    container = tk.Frame(root, bg=bg_color, padx=40, pady=40)
    container.pack(fill=tk.BOTH, expand=True)
    
    # Títulos
    lbl_brand = tk.Label(container, text="TRAFFIC SIMULATOR", 
                        font=("Segoe UI", 18, "bold"), bg=bg_color, fg=text_main)
    lbl_brand.pack(pady=(0, 5))
    
    lbl_sub = tk.Label(container, text="Seleccione el modo de ejecución", 
                      font=("Segoe UI", 11), bg=bg_color, fg=text_sec)
    lbl_sub.pack(pady=(0, 30))
    
    # Frame Botones
    btn_frame = tk.Frame(container, bg=bg_color)
    btn_frame.pack(fill=tk.X, pady=10)
    
    # Función factory para botones estilizados
    def crear_boton(parent, text, color, cmd, icon="🚀"):
        f = tk.Frame(parent, bg=color, padx=2, pady=2) # Borde simulado
        b = tk.Button(f, text=f"{icon}  {text}", 
                     font=("Segoe UI", 11, "bold"),
                     bg=color, fg="white",
                     activebackground="white", activeforeground=color,
                     relief=tk.FLAT, bd=0, cursor="hand2",
                     width=16, height=2,
                     command=cmd)
        b.pack(fill=tk.BOTH, expand=True)
        # Efecto hover simple
        def on_enter(e): b['bg'] = "#ffffff"; b['fg'] = color
        def on_leave(e): b['bg'] = color; b['fg'] = "white"
        b.bind("<Enter>", on_enter)
        b.bind("<Leave>", on_leave)
        return f
    
    # Botón Procesos (Izquierda)
    btn_p_con = crear_boton(btn_frame, "PROCESOS", accent_blue, 
                           lambda: [modo_seleccionado.__setitem__(0, MODO_PROCESOS), root.quit()], "⚙️")
    btn_p_con.pack(side=tk.LEFT, padx=(0, 10), expand=True)

    # Botón Hilos (Derecha)
    btn_h_con = crear_boton(btn_frame, "HILOS", accent_green, 
                           lambda: [modo_seleccionado.__setitem__(0, MODO_HILOS), root.quit()], "⚡")
    btn_h_con.pack(side=tk.RIGHT, padx=(10, 0), expand=True)
    
    # Tarjeta de Información
    info_card = tk.LabelFrame(container, text=" Detalles Técnicos ", 
                             font=("Segoe UI", 9, "bold"), fg=text_sec,
                             bg=bg_color, bd=1, relief=tk.SOLID)
    info_card.config(fg="#475569") # Color del borde del texto
    # Tkinter LabelFrame border color es dificil, usamos Frame simulado mejor
    
    info_frame = tk.Frame(container, bg=card_bg, padx=15, pady=15)
    info_frame.pack(fill=tk.X, pady=(30, 0))
    
    tk.Label(info_frame, text="• Procesos:", font=("Segoe UI", 9, "bold"), bg=card_bg, fg=text_main).pack(anchor="w")
    tk.Label(info_frame, text="  Memoria independiente, ideal para CPU-bound.", font=("Segoe UI", 9), bg=card_bg, fg=text_sec).pack(anchor="w", pady=(0, 5))
    
    tk.Label(info_frame, text="• Hilos:", font=("Segoe UI", 9, "bold"), bg=card_bg, fg=text_main).pack(anchor="w")
    tk.Label(info_frame, text="  Memoria compartida, bajo consumo de recursos.", font=("Segoe UI", 9), bg=card_bg, fg=text_sec).pack(anchor="w")
    
    root.mainloop()
    root.destroy()
    
    return modo_seleccionado[0]

def ejecutar_simulacion(modo_elegido):
    """Ejecuta la simulación con el modo seleccionado"""
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
    
    # Evento para activar ambulancia (compartido entre todos)
    evento_ambulancia = ManagerEvent()
    evento_ambulancia_activa = ManagerEvent()  # Indica si hay ambulancia activa
    
    # Dirección de la ambulancia - usar Value para procesos, dict para threads
    if modo_elegido == MODO_PROCESOS:
        direccion_ambulancia = multiprocessing.Value('c', b'N')
    else:
        direccion_ambulancia = {'value': 'N', 'lock': threading.Lock()}

    workers = []
    
    # Lanzar semáforos (NUM_SEMAFOROS workers)
    semaforos_ids = ['N', 'S', 'E', 'O']  # Debe coincidir con NUM_SEMAFOROS
    for sem_id in semaforos_ids:
        w = WorkerClass(target=tarea_semaforo, 
                        args=(sem_id, eventos_inicio[sem_id], eventos_fin[sem_id], cola_gui, modo_elegido, evento_ambulancia, evento_ambulancia_activa, direccion_ambulancia))
        w.daemon = True
        w.start()
        workers.append(w)

    # Lanzar controlador (NUM_CONTROLADORES workers)
    for _ in range(NUM_CONTROLADORES):
        ctrl = WorkerClass(target=tarea_controlador, 
                           args=(eventos_inicio, eventos_fin, cola_gui, evento_ambulancia, evento_ambulancia_activa, direccion_ambulancia))
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
    app = TrafficApp(root, cola_gui, modo_elegido, workers, evento_ambulancia, evento_ambulancia_activa, direccion_ambulancia)
    root.mainloop()
    
    # Limpiar workers restantes si la ventana se cerró sin usar el botón
    if workers:
        print("\nLimpiando workers restantes...")
        for worker in workers:
            if worker.is_alive():
                if modo_elegido == MODO_PROCESOS and isinstance(worker, multiprocessing.Process):
                    worker.terminate()
                # Los hilos daemon se terminarán automáticamente

def main():
    # Configurar multiprocessing para Windows
    if sys.platform == 'win32':
        multiprocessing.set_start_method('spawn', force=True)
    
    # Bucle principal: permite volver a seleccionar modo
    while True:
        # Mostrar diálogo de selección de modo
        modo_elegido = seleccionar_modo()
        
        # Si el usuario cierra la ventana de selección sin elegir, salir
        if modo_elegido is None:
            break
        
        # Ejecutar simulación
        ejecutar_simulacion(modo_elegido)
        
        # Después de cerrar la simulación, volver a mostrar selección
        # (el bucle while se repite automáticamente)

if __name__ == "__main__":
    main()

