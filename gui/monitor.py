import tkinter as tk
from tkinter import ttk
import threading
import multiprocessing
import os
import sys
from config import MODO_PROCESOS, MODO_HILOS

class MonitorPanel:
    """Panel de monitoreo para visualizar hilos y procesos activos"""
    
    def __init__(self, parent, modo, workers=None):
        self.parent = parent
        self.modo = modo
        self.workers = workers or []
        self.window = None
        self.running = True
        
    def crear_ventana(self):
        """Crea la ventana de monitoreo estilo Cyber-Dashboard"""
        from config import THEME_BG, THEME_BG_SEC, THEME_FG, THEME_FG_SEC, THEME_ACCENT, THEME_BORDER, UI_SUCCESS, UI_INFO, UI_WARNING
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("System Monitor - Realtime Analytics")
        self.window.geometry("900x700")
        self.window.configure(bg=THEME_BG)
        self.window.protocol("WM_DELETE_WINDOW", self.cerrar)
        
        # Container principal con padding
        main_container = tk.Frame(self.window, bg=THEME_BG, padx=30, pady=30)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Header limpio
        header = tk.Frame(main_container, bg=THEME_BG)
        header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header, text="SYSTEM MONITOR", font=("Segoe UI", 24, "bold"), 
                bg=THEME_BG, fg=THEME_FG).pack(anchor="w")
        tk.Label(header, text=f"Execution Mode: {self.modo}", font=("Segoe UI", 12), 
                bg=THEME_BG, fg=THEME_ACCENT).pack(anchor="w")
        
        # Info Card (Glass style)
        self.crear_info_sistema(main_container)
        
        # Separador / Título de Grid
        tk.Label(main_container, text="ACTIVE WORKERS STATUS", font=("Segoe UI", 10, "bold"), 
                bg=THEME_BG, fg=THEME_FG_SEC).pack(anchor="w", pady=(20, 10))
        
        # Grid para workers (3 columnas x 2 filas)
        self.grid_frame = tk.Frame(main_container, bg=THEME_BG)
        self.grid_frame.pack(fill=tk.BOTH, expand=True)
        
        self.worker_frames = {}
        self.actualizar_monitoreo()
        
    def crear_info_sistema(self, parent):
        """Crea sección de información del sistema estilo Cyber"""
        from config import THEME_BG_SEC, THEME_FG, THEME_FG_SEC, UI_SUCCESS, UI_INFO
        
        # Card container
        info_card = tk.Frame(parent, bg=THEME_BG_SEC, padx=20, pady=20)
        info_card.pack(fill=tk.X)
        
        # PID Principal
        pid_principal = os.getpid()
        
        # Layout de 2 columnas para info
        row1 = tk.Frame(info_card, bg=THEME_BG_SEC)
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="Main Process PID:", font=("Segoe UI", 10), bg=THEME_BG_SEC, fg=THEME_FG_SEC).pack(side=tk.LEFT)
        tk.Label(row1, text=str(pid_principal), font=("Segoe UI", 10, "bold"), bg=THEME_BG_SEC, fg=THEME_FG).pack(side=tk.RIGHT)
        
        # Info Modo
        row2 = tk.Frame(info_card, bg=THEME_BG_SEC)
        row2.pack(fill=tk.X, pady=2)
        
        if self.modo == MODO_HILOS:
            num_hilos = threading.active_count()
            txt_count = f"{num_hilos} Threads (Shared Memory)"
            col_st = UI_SUCCESS
        else:
            num_workers = len(multiprocessing.active_children())
            txt_count = f"{num_workers + 1} Processes (Isolated Memory)"
            col_st = UI_INFO
            
        tk.Label(row2, text="Concurrency Status:", font=("Segoe UI", 10), bg=THEME_BG_SEC, fg=THEME_FG_SEC).pack(side=tk.LEFT)
        tk.Label(row2, text=txt_count, font=("Segoe UI", 10, "bold"), bg=THEME_BG_SEC, fg=col_st).pack(side=tk.RIGHT)
        
        # GIL Info
        row3 = tk.Frame(info_card, bg=THEME_BG_SEC)
        row3.pack(fill=tk.X, pady=2)
        
        gil_status = "UNKNOWN"
        col_gil = THEME_FG_SEC
        if hasattr(sys, "_is_gil_enabled"):
            enabled = sys._is_gil_enabled()
            gil_status = "ENABLED (Standard)" if enabled else "DISABLED (Free-Threading)"
            col_gil = "#f43f5e" if enabled else "#10b981"
            
        tk.Label(row3, text="Global Interpreter Lock:", font=("Segoe UI", 10), bg=THEME_BG_SEC, fg=THEME_FG_SEC).pack(side=tk.LEFT)
        tk.Label(row3, text=gil_status, font=("Segoe UI", 10, "bold"), bg=THEME_BG_SEC, fg=col_gil).pack(side=tk.RIGHT)
    
    
    def obtener_info_worker(self, worker, index):
        """Obtiene información detallada de un worker"""
        info = {}
        
        if self.modo == MODO_HILOS:
            # Información de hilos
            if isinstance(worker, threading.Thread):
                info['tipo'] = "Hilo"
                info['nombre'] = worker.name
                info['id'] = worker.ident if worker.ident else "N/A"
                info['vivo'] = worker.is_alive()
                info['daemon'] = worker.daemon
                info['pid'] = os.getpid()  # Los hilos comparten el mismo PID
        else:
            # Información de procesos
            if isinstance(worker, multiprocessing.Process):
                info['tipo'] = "Proceso"
                info['nombre'] = worker.name
                info['id'] = worker.pid if worker.pid else "N/A"
                info['vivo'] = worker.is_alive()
                info['daemon'] = worker.daemon
                info['pid'] = worker.pid if worker.pid else "N/A"
        
        # Determinar función basado en el índice
        if index < 4:  # Semáforos
            info['funcion'] = f"Semáforo {['N', 'S', 'E', 'O'][index]}"
        else:  # Controlador
            info['funcion'] = "Controlador"
        
        return info
    
    def actualizar_monitoreo(self):
        """Actualiza la información de los workers en tiempo real (Cyber Style)"""
        from config import THEME_BG, THEME_FG_SEC
        if not self.window or not self.window.winfo_exists():
            return
            
        try:
            # Limpiar grid actual
            for widget in self.grid_frame.winfo_children():
                widget.destroy()
                
            # Recrear recuadro del proceso principal (posición 0,0)
            self.crear_recuadro_cyber(0, 0, None, "Main Controller", is_principal=True)
            
            # Recrear workers
            for i, worker in enumerate(self.workers):
                # Layout Grid:
                if i == 0: row, col = 0, 1
                elif i == 1: row, col = 0, 2
                elif i == 2: row, col = 1, 0
                elif i == 3: row, col = 1, 1
                else: row, col = 1, 2
                
                info = self.obtener_info_worker(worker, i)
                self.crear_recuadro_cyber(row, col, worker, info['funcion'], is_principal=False, worker_index=i)
            
            if not self.workers:
                tk.Label(self.grid_frame, text="No secondary workers active", 
                        font=("Segoe UI", 12), fg=THEME_FG_SEC, bg=THEME_BG).grid(row=0, column=1, columnspan=2, pady=50)
                
        except Exception as e:
            print(f"Error updating monitor: {e}")
            
        if self.running and self.window:
            self.window.after(1000, self.actualizar_monitoreo)
    
    def crear_recuadro_cyber(self, row, col, worker, funcion, is_principal=False, worker_index=None):
        """Crea una 'Glass Card' para un worker"""
        from config import THEME_BG, THEME_BG_SEC, THEME_FG, THEME_FG_SEC, UI_SUCCESS, UI_DANGER, UI_INFO, UI_WARNING, MODO_HILOS
        
        # Color del borde/acento según estado/tipo
        accent_color = UI_WARNING if is_principal else (UI_SUCCESS if self.modo == MODO_HILOS else UI_INFO)
        
        # Frame contenedor (Card)
        card = tk.Frame(self.grid_frame, bg=THEME_BG_SEC, padx=2, pady=2) # Padding simula borde
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        
        # Efecto borde coloreado
        card.configure(bg=accent_color) 
        
        # Contenido interno (Fondo oscuro)
        inner = tk.Frame(card, bg="#1e293b", padx=15, pady=15)
        inner.pack(fill=tk.BOTH, expand=True)

        self.grid_frame.columnconfigure(col, weight=1)
        self.grid_frame.rowconfigure(row, weight=1)
        
        # Icono y Título
        icon = "👑" if is_principal else "⚙️"
        
        header_row = tk.Frame(inner, bg="#1e293b")
        header_row.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_row, text=icon, font=("Segoe UI", 12), bg="#1e293b", fg="white").pack(side=tk.LEFT, padx=(0,5))
        tk.Label(header_row, text=funcion, font=("Segoe UI", 10, "bold"), bg="#1e293b", fg=THEME_FG).pack(side=tk.LEFT)
        
        # Detalles
        details = tk.Frame(inner, bg="#1e293b")
        details.pack(fill=tk.BOTH, expand=True)
        
        def add_detail(lbl, val, val_color=THEME_FG_SEC):
            row_d = tk.Frame(details, bg="#1e293b")
            row_d.pack(fill=tk.X, pady=1)
            tk.Label(row_d, text=lbl, font=("Segoe UI", 9), bg="#1e293b", fg="#64748b").pack(side=tk.LEFT)
            tk.Label(row_d, text=val, font=("Segoe UI", 9, "bold"), bg="#1e293b", fg=val_color).pack(side=tk.RIGHT)

        if is_principal:
            pid = os.getpid()
            add_detail("PID:", str(pid), THEME_FG)
            add_detail("Status:", "ACTIVE", UI_SUCCESS)
        elif worker and worker_index is not None:
             info = self.obtener_info_worker(worker, worker_index)
             
             w_id = info.get('id', 'N/A')
             pid = info.get('pid', 'N/A')
             alive = info.get('vivo', False)
             
             add_detail("ID:", str(w_id), THEME_FG)
             add_detail("PID:", str(pid), THEME_FG)
             add_detail("Status:", "RUNNING" if alive else "STOPPED", UI_SUCCESS if alive else UI_DANGER)
        
        self.worker_frames[(row, col)] = card
    
    def cerrar(self):
        """Cierra la ventana de monitoreo"""
        self.running = False
        if self.window:
            self.window.destroy()
            self.window = None

