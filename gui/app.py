import tkinter as tk
from tkinter import messagebox
from config import (
    ANCHO_VENTANA, ALTO_VENTANA, COLOR_FONDO, COLOR_CALLE, COLOR_LINEA,
    COLOR_AUTO_ESPERA, COLOR_AUTO_CRUZANDO, COLOR_AMBULANCIA, CENTRO_X, CENTRO_Y,
    ANCHO_CALLE, OFFSET_SEMAFORO
)
from models import Estadisticas
from utils import obtener_info_sistema
from gui.monitor import MonitorPanel

# ==========================================
# GUI CON ANIMACIÓN DE AUTOS
# ==========================================

class TrafficApp:
    def __init__(self, root, cola_comunicacion, modo=None, workers=None, evento_ambulancia=None, evento_ambulancia_activa=None, direccion_ambulancia=None):
        self.root = root
        self.cola = cola_comunicacion
        self.modo = modo
        self.workers = workers or []
        self.evento_ambulancia = evento_ambulancia
        self.evento_ambulancia_activa = evento_ambulancia_activa
        self.direccion_ambulancia = direccion_ambulancia
        self.root.title("Simulador de Tráfico Paralelo - UPS Cuenca")
        self.root.geometry("900x700")
        
        self.info_sys = obtener_info_sistema(modo, self.workers)
        self.stats = Estadisticas()
        
        # Estructuras para animación
        self.autos_animados = [] # Lista de autos moviéndose actualmente
        self.colas_graficas = {'N': [], 'S': [], 'E': [], 'O': []} # IDs de rectángulos en espera
        self.ambulancia_activa = False
        self.sirena_parpadeando = False
        self.sirena_activa = False
        
        # Panel de monitoreo
        self.monitor_panel = None
        
        self.setup_ui()
        self.running = True
        
        # Configurar handler para cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Iniciar bucles de la GUI
        self.procesar_mensajes()
        self.bucle_animacion()

    def setup_ui(self):
        # Header Info
        header = tk.Frame(self.root, bg="#ecf0f1", pady=5)
        header.pack(fill=tk.X)
        
        # Frame para info y botón
        header_content = tk.Frame(header, bg="#ecf0f1")
        header_content.pack(fill=tk.X, padx=10)
        
        info_text = (f"Modo: {self.info_sys['modo']} | "
                    f"{self.info_sys['tipo_workers']}: {self.info_sys['num_workers']} | "
                    f"Python: {self.info_sys['python_ver']} | "
                    f"GIL: {self.info_sys['gil_status']}")
        lbl = tk.Label(header_content, text=info_text, 
                       bg="#ecf0f1", font=("Consolas", 10))
        lbl.pack(side=tk.LEFT)
        
        # Frame para botones del header
        btn_frame = tk.Frame(header_content, bg="#ecf0f1")
        btn_frame.pack(side=tk.RIGHT)
        
        # Botón para abrir monitoreo
        btn_monitor = tk.Button(btn_frame, text="📊 Monitoreo", 
                               font=("Arial", 9, "bold"),
                               bg="#3498db", fg="white",
                               relief=tk.RAISED, bd=2,
                               command=self.abrir_monitoreo)
        btn_monitor.pack(side=tk.LEFT, padx=5)
        
        # Botón Ambulancia
        self.btn_ambulancia = tk.Button(btn_frame, text="🚑 Ambulancia", 
                                       font=("Arial", 9, "bold"),
                                       bg="#f39c12", fg="white",
                                       relief=tk.RAISED, bd=2,
                                       command=self.activar_ambulancia)
        self.btn_ambulancia.pack(side=tk.LEFT, padx=5)
        
        # Botón Volver atrás
        btn_volver = tk.Button(btn_frame, text="⬅️ Volver atrás", 
                              font=("Arial", 9, "bold"),
                              bg="#e74c3c", fg="white",
                              relief=tk.RAISED, bd=2,
                              command=self.volver_atras)
        btn_volver.pack(side=tk.LEFT, padx=5)

        # Canvas Principal
        self.canvas = tk.Canvas(self.root, width=ANCHO_VENTANA, height=ALTO_VENTANA, bg=COLOR_FONDO)
        self.canvas.pack(pady=10)
        self.dibujar_calles()
        
        # Inicializar Semáforos Gráficos
        self.sem_graficos = {}
        coords_sem = {
            'N': (CENTRO_X, CENTRO_Y - OFFSET_SEMAFORO - 20),
            'S': (CENTRO_X, CENTRO_Y + OFFSET_SEMAFORO + 20),
            'E': (CENTRO_X + OFFSET_SEMAFORO + 20, CENTRO_Y),
            'O': (CENTRO_X - OFFSET_SEMAFORO - 20, CENTRO_Y)
        }
        
        for k, (x, y) in coords_sem.items():
            luz = self.canvas.create_oval(x-15, y-15, x+15, y+15, fill="red", outline="white", width=2)
            txt = self.canvas.create_text(x, y-25 if k in ['N','E','O'] else y+25, text=f"{k}: 0", fill="white", font=("Arial", 10, "bold"))
            self.sem_graficos[k] = {'luz': luz, 'txt': txt, 'pos': (x, y)}

        # Footer Stats
        self.lbl_stats = tk.Label(self.root, text="Esperando datos...", font=("Arial", 11), bg="#bdc3c7", pady=5)
        self.lbl_stats.pack(fill=tk.X, side=tk.BOTTOM)

    def dibujar_calles(self):
        # Calles
        self.canvas.create_rectangle(CENTRO_X - ANCHO_CALLE/2, 0, CENTRO_X + ANCHO_CALLE/2, ALTO_VENTANA, fill=COLOR_CALLE, outline="")
        self.canvas.create_rectangle(0, CENTRO_Y - ANCHO_CALLE/2, ANCHO_VENTANA, CENTRO_Y + ANCHO_CALLE/2, fill=COLOR_CALLE, outline="")
        
        # Líneas centrales
        self.canvas.create_line(CENTRO_X, 0, CENTRO_X, ALTO_VENTANA, fill=COLOR_LINEA, dash=(15, 10))
        self.canvas.create_line(0, CENTRO_Y, ANCHO_VENTANA, CENTRO_Y, fill=COLOR_LINEA, dash=(15, 10))
        
        # Líneas de parada (Stop lines)
        stop_offset = ANCHO_CALLE/2 + 10
        # Norte
        self.canvas.create_line(CENTRO_X, CENTRO_Y - stop_offset, CENTRO_X - ANCHO_CALLE/2, CENTRO_Y - stop_offset, fill="white", width=3)
        # Sur
        self.canvas.create_line(CENTRO_X, CENTRO_Y + stop_offset, CENTRO_X + ANCHO_CALLE/2, CENTRO_Y + stop_offset, fill="white", width=3)
        # Este
        self.canvas.create_line(CENTRO_X + stop_offset, CENTRO_Y, CENTRO_X + stop_offset, CENTRO_Y - ANCHO_CALLE/2, fill="white", width=3)
        # Oeste
        self.canvas.create_line(CENTRO_X - stop_offset, CENTRO_Y, CENTRO_X - stop_offset, CENTRO_Y + ANCHO_CALLE/2, fill="white", width=3)

    def procesar_mensajes(self):
        try:
            while not self.cola.empty():
                msg = self.cola.get_nowait()
                tipo = msg[0]
                
                if tipo == "UPDATE":
                    _, id_sem, color, num_autos = msg
                    self.canvas.itemconfig(self.sem_graficos[id_sem]['luz'], fill=color)
                    self.canvas.itemconfig(self.sem_graficos[id_sem]['txt'], text=f"{id_sem}: {num_autos}")
                    self.actualizar_cola_visual(id_sem, num_autos)
                    # Asegurar que el texto y la luz del semáforo siempre estén encima
                    self.canvas.tag_raise(self.sem_graficos[id_sem]['txt'])
                    self.canvas.tag_raise(self.sem_graficos[id_sem]['luz'])
                    
                elif tipo == "ANIMACION_CRUCE":
                    _, id_sem = msg
                    self.generar_auto_cruzando(id_sem)
                    
                elif tipo == "STATS":
                    self.stats.registrar_cruce(msg[1])
                    prom = self.stats.tiempo_total_espera / self.stats.total_vehiculos
                    self.lbl_stats.config(text=f"Total Autos: {self.stats.total_vehiculos} | Tiempo Espera Promedio: {prom:.2f}s | Ciclo Actual")

                elif tipo == "CICLO":
                    self.root.title(f"Simulador de Tráfico - Ciclo {msg[1]}")
                
                elif tipo == "FIN":
                    messagebox.showinfo("Fin", "Simulación Completada")
                
                elif tipo == "AMBULANCIA_CRUZANDO":
                    _, id_sem = msg
                    self.ambulancia_activa = True
                    self.sirena_activa = True
                    self.generar_ambulancia_cruzando(id_sem)
                    self.iniciar_efecto_sirena()
                
                elif tipo == "AMBULANCIA_COMPLETADA":
                    _, id_sem = msg
                    self.ambulancia_activa = False
                    self.sirena_activa = False
                    self.detener_efecto_sirena()
                    self.btn_ambulancia.config(state=tk.NORMAL)
                    
        except Exception:
            pass
        
        if self.running:
            self.root.after(50, self.procesar_mensajes)

    def actualizar_cola_visual(self, id_sem, cantidad):
        """Dibuja rectángulos estáticos representando la cola de espera"""
        # Limpiar cola anterior
        for item in self.colas_graficas[id_sem]:
            self.canvas.delete(item)
        self.colas_graficas[id_sem] = []
        
        # Parámetros de dibujo
        w_auto, h_auto = 20, 30
        gap = 5
        stop_dist = ANCHO_CALLE/2 + 15
        
        # Limitar visualización a 10 autos para no saturar
        cantidad_visible = min(cantidad, 12)
        
        for i in range(cantidad_visible):
            if id_sem == 'N': # Cola hacia arriba
                x = CENTRO_X - ANCHO_CALLE/4
                y = (CENTRO_Y - stop_dist) - (i * (h_auto + gap)) - h_auto
                rect = self.canvas.create_rectangle(x-10, y, x+10, y+h_auto, fill=COLOR_AUTO_ESPERA, outline="black")
            elif id_sem == 'S': # Cola hacia abajo
                x = CENTRO_X + ANCHO_CALLE/4
                y = (CENTRO_Y + stop_dist) + (i * (h_auto + gap))
                rect = self.canvas.create_rectangle(x-10, y, x+10, y+h_auto, fill=COLOR_AUTO_ESPERA, outline="black")
            elif id_sem == 'E': # Cola hacia derecha
                x = (CENTRO_X + stop_dist) + (i * (h_auto + gap))
                y = CENTRO_Y - ANCHO_CALLE/4
                rect = self.canvas.create_rectangle(x, y-10, x+h_auto, y+10, fill=COLOR_AUTO_ESPERA, outline="black")
            elif id_sem == 'O': # Cola hacia izquierda
                x = (CENTRO_X - stop_dist) - (i * (h_auto + gap)) - h_auto
                y = CENTRO_Y + ANCHO_CALLE/4
                rect = self.canvas.create_rectangle(x, y-10, x+h_auto, y+10, fill=COLOR_AUTO_ESPERA, outline="black")
            
            self.colas_graficas[id_sem].append(rect)
        
        # Asegurar que el texto y la luz del semáforo siempre estén encima de los autos
        self.canvas.tag_raise(self.sem_graficos[id_sem]['txt'])
        self.canvas.tag_raise(self.sem_graficos[id_sem]['luz'])

    def generar_auto_cruzando(self, id_sem):
        """Crea un auto animado que cruza la intersección"""
        w, h = 20, 30
        vx, vy = 0, 0
        
        # Determinar posición inicial y velocidad según dirección
        if id_sem == 'N': # Baja
            x = CENTRO_X - ANCHO_CALLE/4
            y = CENTRO_Y - ANCHO_CALLE/2 - 20
            vx, vy = 0, 8
            rect = self.canvas.create_rectangle(x-10, y, x+10, y+h, fill=COLOR_AUTO_CRUZANDO)
        elif id_sem == 'S': # Sube
            x = CENTRO_X + ANCHO_CALLE/4
            y = CENTRO_Y + ANCHO_CALLE/2 + 20
            vx, vy = 0, -8
            rect = self.canvas.create_rectangle(x-10, y-h, x+10, y, fill=COLOR_AUTO_CRUZANDO)
        elif id_sem == 'E': # Va a izquierda
            x = CENTRO_X + ANCHO_CALLE/2 + 20
            y = CENTRO_Y - ANCHO_CALLE/4
            vx, vy = -8, 0
            rect = self.canvas.create_rectangle(x, y-10, x+h, y+10, fill=COLOR_AUTO_CRUZANDO)
        elif id_sem == 'O': # Va a derecha
            x = CENTRO_X - ANCHO_CALLE/2 - 20
            y = CENTRO_Y + ANCHO_CALLE/4
            vx, vy = 8, 0
            rect = self.canvas.create_rectangle(x-h, y-10, x, y+10, fill=COLOR_AUTO_CRUZANDO)
            
        self.autos_animados.append({'id': rect, 'vx': vx, 'vy': vy})

    def bucle_animacion(self):
        """Actualiza la posición de los autos animados"""
        por_eliminar = []
        
        for auto in self.autos_animados:
            # Mover el rectángulo
            self.canvas.move(auto['id'], auto['vx'], auto['vy'])
            
            # Si es ambulancia, mover también el texto
            if 'texto' in auto:
                self.canvas.move(auto['texto'], auto['vx'], auto['vy'])
            
            coords = self.canvas.coords(auto['id'])
            
            # Verificar si salió de la pantalla
            if (coords[2] < 0 or coords[0] > ANCHO_VENTANA or 
                coords[3] < 0 or coords[1] > ALTO_VENTANA):
                por_eliminar.append(auto)
        
        # Limpieza
        for auto in por_eliminar:
            self.canvas.delete(auto['id'])
            if 'texto' in auto:  # Si es ambulancia, eliminar también el texto
                self.canvas.delete(auto['texto'])
            self.autos_animados.remove(auto)
        
        # Asegurar que todos los textos de semáforos siempre estén encima
        for sem_id in self.sem_graficos:
            self.canvas.tag_raise(self.sem_graficos[sem_id]['txt'])
            self.canvas.tag_raise(self.sem_graficos[sem_id]['luz'])
            
        if self.running:
            self.root.after(30, self.bucle_animacion)
    
    def abrir_monitoreo(self):
        """Abre el panel de monitoreo"""
        if self.monitor_panel is None or (self.monitor_panel.window is None or not self.monitor_panel.window.winfo_exists()):
            self.monitor_panel = MonitorPanel(self.root, self.modo, self.workers)
            self.monitor_panel.crear_ventana()
        else:
            # Si ya está abierto, traerlo al frente
            self.monitor_panel.window.lift()
            self.monitor_panel.window.focus_force()
    
    def activar_ambulancia(self):
        """Activa una ambulancia desde una dirección aleatoria"""
        import random
        
        if self.ambulancia_activa:
            return  # Ya hay una ambulancia activa
        
        # Deshabilitar botón mientras la ambulancia está activa
        self.btn_ambulancia.config(state=tk.DISABLED)
        
        # Seleccionar dirección aleatoria
        direcciones = ['N', 'S', 'E', 'O']
        direccion = random.choice(direcciones)
        
        # Establecer dirección en el objeto compartido
        if self.direccion_ambulancia:
            if hasattr(self.direccion_ambulancia, 'value'):  # Multiprocessing Value
                self.direccion_ambulancia.value = direccion.encode() if isinstance(direccion, str) else direccion
            elif isinstance(self.direccion_ambulancia, dict):  # Dict para threads
                if 'lock' in self.direccion_ambulancia:
                    with self.direccion_ambulancia['lock']:
                        self.direccion_ambulancia['value'] = direccion
                else:
                    self.direccion_ambulancia['value'] = direccion
        
        # Activar eventos de ambulancia
        if self.evento_ambulancia_activa:
            self.evento_ambulancia_activa.set()
        if self.evento_ambulancia:
            self.evento_ambulancia.set()
        
        print(f"\n🚑 AMBULANCIA ACTIVADA desde dirección: {direccion}")
    
    def generar_ambulancia_cruzando(self, id_sem):
        """Crea una ambulancia animada que cruza la intersección con prioridad"""
        w, h = 25, 35  # Ambulancia más grande
        vx, vy = 0, 0
        
        # Determinar posición inicial y velocidad según dirección
        if id_sem == 'N': # Baja
            x = CENTRO_X - ANCHO_CALLE/4
            y = CENTRO_Y - ANCHO_CALLE/2 - 20
            vx, vy = 0, 10  # Más rápida
            rect = self.canvas.create_rectangle(x-12, y, x+12, y+h, fill=COLOR_AMBULANCIA, outline="white", width=2)
        elif id_sem == 'S': # Sube
            x = CENTRO_X + ANCHO_CALLE/4
            y = CENTRO_Y + ANCHO_CALLE/2 + 20
            vx, vy = 0, -10
            rect = self.canvas.create_rectangle(x-12, y-h, x+12, y, fill=COLOR_AMBULANCIA, outline="white", width=2)
        elif id_sem == 'E': # Va a izquierda
            x = CENTRO_X + ANCHO_CALLE/2 + 20
            y = CENTRO_Y - ANCHO_CALLE/4
            vx, vy = -10, 0
            rect = self.canvas.create_rectangle(x, y-12, x+h, y+12, fill=COLOR_AMBULANCIA, outline="white", width=2)
        elif id_sem == 'O': # Va a derecha
            x = CENTRO_X - ANCHO_CALLE/2 - 20
            y = CENTRO_Y + ANCHO_CALLE/4
            vx, vy = 10, 0
            rect = self.canvas.create_rectangle(x-h, y-12, x, y+12, fill=COLOR_AMBULANCIA, outline="white", width=2)
        
        # Añadir texto "AMB" en la ambulancia
        texto_amb = self.canvas.create_text(x, y, text="AMB", fill="white", font=("Arial", 8, "bold"))
        
        self.autos_animados.append({'id': rect, 'vx': vx, 'vy': vy, 'es_ambulancia': True, 'texto': texto_amb})
    
    def iniciar_efecto_sirena(self):
        """Inicia el efecto visual de sirena parpadeando"""
        self.sirena_parpadeando = True
        self.parpadear_sirena()
    
    def parpadear_sirena(self):
        """Efecto de parpadeo para simular sirena"""
        if not self.sirena_activa or not self.sirena_parpadeando:
            return
        
        # Cambiar color de fondo del canvas alternativamente
        color_actual = self.canvas.cget("bg")
        if color_actual == COLOR_FONDO:
            self.canvas.config(bg="#ffeb3b")
        else:
            self.canvas.config(bg=COLOR_FONDO)
        
        # Continuar parpadeando
        if self.sirena_parpadeando and self.sirena_activa:
            self.root.after(200, self.parpadear_sirena)
    
    def detener_efecto_sirena(self):
        """Detiene el efecto de sirena"""
        self.sirena_parpadeando = False
        self.canvas.config(bg=COLOR_FONDO)  # Restaurar color original
    
    def terminar_workers(self):
        """Termina todos los workers (procesos/hilos) de forma segura"""
        import multiprocessing
        import threading
        from config import MODO_PROCESOS
        
        if not self.workers:
            return
        
        print(f"\n{'='*60}")
        print("Terminando workers...")
        print(f"{'='*60}")
        
        # Cerrar panel de monitoreo si está abierto
        if self.monitor_panel and self.monitor_panel.window:
            self.monitor_panel.cerrar()
        
        # Terminar cada worker
        for i, worker in enumerate(self.workers):
            try:
                if worker.is_alive():
                    if self.modo == MODO_PROCESOS:
                        # Para procesos, usar terminate() que es más rápido
                        if isinstance(worker, multiprocessing.Process):
                            worker.terminate()
                            print(f"  Worker {i+1} ({worker.name}): Proceso terminado")
                    else:
                        # Para hilos, no hay método directo de terminación
                        # Los hilos daemon se terminarán cuando termine el proceso principal
                        print(f"  Worker {i+1} ({worker.name}): Hilo daemon (se terminará automáticamente)")
            except Exception as e:
                print(f"  Error terminando worker {i+1}: {e}")
        
        # Esperar a que los procesos terminen (con timeout)
        if self.modo == MODO_PROCESOS:
            import time
            for worker in self.workers:
                if isinstance(worker, multiprocessing.Process) and worker.is_alive():
                    try:
                        worker.join(timeout=2.0)  # Esperar máximo 2 segundos
                        if worker.is_alive():
                            print(f"  Advertencia: Worker {worker.name} no terminó en el tiempo esperado")
                    except Exception as e:
                        print(f"  Error esperando worker: {e}")
        
        print(f"{'='*60}\n")
        self.workers.clear()
    
    def on_closing(self):
        """Maneja el cierre de la ventana (X o botón volver atrás)"""
        # Detener bucles de la GUI
        self.running = False
        
        # Terminar todos los workers
        self.terminar_workers()
        
        # Cerrar ventana actual
        self.root.quit()
        self.root.destroy()
    
    def volver_atras(self):
        """Vuelve a la ventana de selección de modo, terminando todos los workers"""
        # Confirmar acción
        respuesta = messagebox.askyesno(
            "Volver atrás",
            "¿Está seguro de que desea volver a la selección de modo?\n\n"
            "Esto detendrá la simulación actual y todos los procesos/hilos activos."
        )
        
        if not respuesta:
            return
        
        # Usar el mismo handler de cierre
        self.on_closing()

