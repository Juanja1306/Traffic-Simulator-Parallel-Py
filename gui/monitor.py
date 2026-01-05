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
        """Crea la ventana de monitoreo"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Monitoreo - Hilos/Procesos")
        self.window.geometry("900x700")
        self.window.protocol("WM_DELETE_WINDOW", self.cerrar)
        
        # Header mejorado
        header = tk.Frame(self.window, bg="#2c3e50", pady=15)
        header.pack(fill=tk.X)
        
        titulo = tk.Label(header, text="📊 Panel de Monitoreo", 
                         font=("Arial", 16, "bold"), 
                         bg="#2c3e50", fg="white")
        titulo.pack()
        
        modo_label = tk.Label(header, text=f"Modo: {self.modo}", 
                             font=("Arial", 11, "bold"), 
                             bg="#2c3e50", fg="#ecf0f1")
        modo_label.pack(pady=(5, 0))
        
        # Frame principal sin scroll (layout fijo 3x2)
        main_frame = tk.Frame(self.window, bg="#ecf0f1")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Información del sistema (encabezado)
        self.crear_info_sistema(main_frame)
        
        # Grid para workers (3 columnas x 2 filas)
        self.grid_frame = tk.Frame(main_frame, bg="#ecf0f1")
        self.grid_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Inicializar estructura para los recuadros
        self.worker_frames = {}
        
        # Iniciar actualización
        self.actualizar_monitoreo()
        
    def crear_info_sistema(self, parent):
        """Crea sección de información del sistema"""
        frame_info = tk.Frame(parent, bg="#34495e", relief=tk.RAISED, bd=2)
        frame_info.pack(fill=tk.X, pady=(0, 10))
        
        # Contenedor interno con padding
        inner_frame = tk.Frame(frame_info, bg="#34495e", padx=15, pady=12)
        inner_frame.pack(fill=tk.X)
        
        # PID del proceso principal
        pid_principal = os.getpid()
        tk.Label(inner_frame, text=f"🔹 PID Principal: {pid_principal}", 
                font=("Consolas", 10, "bold"), anchor="w", 
                bg="#34495e", fg="white").pack(fill=tk.X, pady=3)
        
        # Información específica del modo
        if self.modo == MODO_HILOS:
            num_workers = len(self.workers) if self.workers else threading.active_count() - 1
            num_hilos = threading.active_count()
            tk.Label(inner_frame, text=f"🔹 Hilos Totales: {num_hilos} (1 principal + {num_workers} workers)", 
                    font=("Consolas", 10, "bold"), anchor="w", 
                    bg="#34495e", fg="#2ecc71").pack(fill=tk.X, pady=3)
            tk.Label(inner_frame, text="ℹ️  Hilos comparten memoria y espacio de proceso", 
                    font=("Consolas", 9), anchor="w", 
                    bg="#34495e", fg="#bdc3c7").pack(fill=tk.X, pady=2)
        else:
            num_workers = len(multiprocessing.active_children())
            num_procesos = num_workers + 1  # +1 para el principal
            tk.Label(inner_frame, text=f"🔹 Procesos Totales: {num_procesos} (1 principal + {num_workers} workers)", 
                    font=("Consolas", 10, "bold"), anchor="w", 
                    bg="#34495e", fg="#3498db").pack(fill=tk.X, pady=3)
            tk.Label(inner_frame, text="ℹ️  Procesos tienen memoria aislada", 
                    font=("Consolas", 9), anchor="w", 
                    bg="#34495e", fg="#bdc3c7").pack(fill=tk.X, pady=2)
        
        # Información del GIL
        if hasattr(sys, "_is_gil_enabled"):
            gil_status = "DESHABILITADO" if not sys._is_gil_enabled() else "Habilitado"
            color_gil = "#2ecc71" if not sys._is_gil_enabled() else "#e74c3c"
            tk.Label(inner_frame, text=f"🔹 GIL: {gil_status}", 
                    font=("Consolas", 10, "bold"), anchor="w", 
                    bg="#34495e", fg=color_gil).pack(fill=tk.X, pady=3)
    
    
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
        """Actualiza la información del monitoreo en layout 3x2"""
        if not self.running or not self.window:
            return
        
        try:
            # Limpiar frames anteriores
            for widget in self.grid_frame.winfo_children():
                widget.destroy()
            self.worker_frames.clear()
            
            # Crear recuadros en grid 3x2 (6 total: 1 principal + 5 workers)
            # Primero el proceso principal (posición 0,0)
            self.crear_recuadro_worker(0, 0, None, "Proceso Principal", is_principal=True, worker_index=None)
            
            # Luego los 5 workers
            for i, worker in enumerate(self.workers):
                # Distribuir en grid: principal en (0,0), workers en:
                # (0,1), (0,2), (1,0), (1,1), (1,2)
                if i == 0:
                    row, col = 0, 1
                elif i == 1:
                    row, col = 0, 2
                elif i == 2:
                    row, col = 1, 0
                elif i == 3:
                    row, col = 1, 1
                else:  # i == 4
                    row, col = 1, 2
                
                info = self.obtener_info_worker(worker, i)
                self.crear_recuadro_worker(row, col, worker, info['funcion'], is_principal=False, worker_index=i)
            
            # Si no hay workers, mostrar mensaje
            if not self.workers:
                msg = tk.Label(self.grid_frame, text="No hay workers activos", 
                              font=("Arial", 12), fg="#7f8c8d", bg="#ecf0f1")
                msg.grid(row=0, column=0, columnspan=3, pady=50)
        
        except Exception as e:
            print(f"Error actualizando monitoreo: {e}")
        
        # Programar próxima actualización
        if self.running and self.window:
            self.window.after(1000, self.actualizar_monitoreo)
    
    def crear_recuadro_worker(self, row, col, worker, funcion, is_principal=False, worker_index=None):
        """Crea un recuadro para un worker en la posición row, col"""
        # Frame principal del recuadro
        worker_frame = tk.Frame(self.grid_frame, relief=tk.RAISED, bd=2, 
                               bg="#ffffff", padx=10, pady=10)
        worker_frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        
        # Configurar peso de columnas para que se expandan
        self.grid_frame.columnconfigure(col, weight=1)
        self.grid_frame.rowconfigure(row, weight=1)
        
        # Color de fondo según tipo
        if is_principal:
            bg_color = "#f39c12"  # Naranja para principal
            border_color = "#e67e22"
        elif self.modo == MODO_HILOS:
            bg_color = "#d5f4e6"  # Verde claro para hilos
            border_color = "#2ecc71"
        else:
            bg_color = "#d6eaf8"  # Azul claro para procesos
            border_color = "#3498db"
        
        # Frame interno con color
        inner_frame = tk.Frame(worker_frame, bg=bg_color, relief=tk.SOLID, bd=2)
        inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo_text = f"🔹 {funcion}"
        if not is_principal and worker and worker_index is not None:
            info = self.obtener_info_worker(worker, worker_index)
            titulo_text += f" ({info['tipo']})"
        
        titulo = tk.Label(inner_frame, text=titulo_text, 
                         font=("Arial", 11, "bold"), 
                         bg=bg_color, fg="#2c3e50")
        titulo.pack(pady=(8, 5))
        
        # Detalles
        detalles_frame = tk.Frame(inner_frame, bg=bg_color)
        detalles_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        if is_principal:
            # Información del proceso principal
            pid_principal = os.getpid()
            tk.Label(detalles_frame, text=f"PID: {pid_principal}", 
                    font=("Consolas", 10, "bold"), bg=bg_color, 
                    fg="#2c3e50", anchor="w").pack(fill=tk.X, pady=3)
            tk.Label(detalles_frame, text="Estado: ✅ Activo", 
                    font=("Consolas", 9, "bold"), bg=bg_color, 
                    fg="#27ae60", anchor="w").pack(fill=tk.X, pady=2)
        elif worker and worker_index is not None:
            info = self.obtener_info_worker(worker, worker_index)
            
            if self.modo == MODO_HILOS:
                tk.Label(detalles_frame, text=f"Thread ID: {info['id']}", 
                        font=("Consolas", 9, "bold"), bg=bg_color, 
                        fg="#2c3e50", anchor="w").pack(fill=tk.X, pady=2)
                tk.Label(detalles_frame, text=f"PID: {info['pid']}", 
                        font=("Consolas", 9), bg=bg_color, 
                        fg="#7f8c8d", anchor="w").pack(fill=tk.X, pady=1)
            else:
                tk.Label(detalles_frame, text=f"Process ID: {info['id']}", 
                        font=("Consolas", 9, "bold"), bg=bg_color, 
                        fg="#2c3e50", anchor="w").pack(fill=tk.X, pady=2)
                tk.Label(detalles_frame, text=f"PID: {info['pid']}", 
                        font=("Consolas", 9), bg=bg_color, 
                        fg="#7f8c8d", anchor="w").pack(fill=tk.X, pady=1)
            
            tk.Label(detalles_frame, text=f"Nombre: {info['nombre']}", 
                    font=("Consolas", 8), bg=bg_color, 
                    fg="#7f8c8d", anchor="w").pack(fill=tk.X, pady=1)
            
            estado_text = "✅ Vivo" if info['vivo'] else "❌ Muerto"
            estado_color = "#27ae60" if info['vivo'] else "#e74c3c"
            tk.Label(detalles_frame, text=f"Estado: {estado_text}", 
                    font=("Consolas", 9, "bold"), bg=bg_color, 
                    fg=estado_color, anchor="w").pack(fill=tk.X, pady=2)
            
            tk.Label(detalles_frame, text=f"Daemon: {'Sí' if info['daemon'] else 'No'}", 
                    font=("Consolas", 8), bg=bg_color, 
                    fg="#7f8c8d", anchor="w").pack(fill=tk.X, pady=1)
        
        self.worker_frames[(row, col)] = worker_frame  # Actualizar cada segundo
    
    def cerrar(self):
        """Cierra la ventana de monitoreo"""
        self.running = False
        if self.window:
            self.window.destroy()
            self.window = None

