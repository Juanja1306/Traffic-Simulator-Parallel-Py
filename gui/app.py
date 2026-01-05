import tkinter as tk
from tkinter import messagebox
import os

# Intentar importar PIL, si no está disponible usar tkinter directamente
try:
    from PIL import Image, ImageTk
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False
from config import (
    ANCHO_VENTANA, ALTO_VENTANA, COLOR_FONDO, COLOR_CALLE, COLOR_LINEA,
    COLOR_AUTO_ESPERA, COLOR_AUTO_CRUZANDO, COLOR_AMBULANCIA, CENTRO_X, CENTRO_Y,
    ANCHO_CALLE, OFFSET_SEMAFORO, COLOR_SEMAFORO_CUERPO, COLOR_LUZ_OFF, COLOR_LUZ_ROJA
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
        
        # Panel de vistas de imágenes
        self.vista_imagenes_panel = None
        
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
        
        # Botón para abrir vistas de imágenes
        btn_vistas = tk.Button(btn_frame, text="🖼️ Vistas", 
                              font=("Arial", 9, "bold"),
                              bg="#9b59b6", fg="white",
                              relief=tk.RAISED, bd=2,
                              command=self.abrir_vistas)
        btn_vistas.pack(side=tk.LEFT, padx=5)
        
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
        
        # Inicializar Semáforos Gráficos (Diseño Moderno)
        self.sem_graficos = {}
        # Ajustamos un poco las posiciones para que el cuerpo del semáforo no invada la calle
        offset_visual = OFFSET_SEMAFORO + 15
        coords_sem = {
            'N': (CENTRO_X, CENTRO_Y - offset_visual),
            'S': (CENTRO_X, CENTRO_Y + offset_visual),
            'E': (CENTRO_X + offset_visual, CENTRO_Y),
            'O': (CENTRO_X - offset_visual, CENTRO_Y)
        }
        
        from config import COLOR_SEMAFORO_CUERPO, COLOR_LUZ_OFF, COLOR_LUZ_ROJA
        
        for k, (x, y) in coords_sem.items():
            # Crear grupo visual para el semáforo
            wm, hm = 16, 40 # Ancho y alto medio del cuerpo
            
        for k, (x, y) in coords_sem.items():
            # Crear semáforo realista con 3 luces
            is_vertical = k in ['N', 'S']
            
            # Dimensiones del cuerpo (Vertical vs Horizontal)
            # Ancho/Alto un poco más grande para albergar 3 luces de radio ~10-12
            if is_vertical:
                w_body, h_body = 34, 90
            else:
                w_body, h_body = 90, 34
                
            x1, y1 = x - w_body/2, y - h_body/2
            x2, y2 = x + w_body/2, y + h_body/2
            
            # Cuerpo negro
            body = self.canvas.create_rectangle(x1, y1, x2, y2, 
                                              fill="#1a1a1a", outline="#444", width=2)
            
            # Configuración de luces
            r_luz = 11  # Radio de la luz
            spacing = 28 # Espaciado entre centros de luces
            
            # Definir posiciones relativas (dx, dy) según orientación
            # Vertical: Rojo arriba, Amarillo centro, Verde abajo
            # Horizontal: Rojo izquierda, Amarillo centro, Verde derecha
            if is_vertical:
                positions = {
                    'red': (0, -spacing),
                    'yellow': (0, 0),
                    'green': (0, spacing)
                }
            else:
                positions = {
                    'red': (-spacing, 0),
                    'yellow': (0, 0),
                    'green': (spacing, 0)
                }
            
            lights = {}
            for color_key, (dx, dy) in positions.items():
                cx, cy = x + dx, y + dy
                # Crear luz apagada (COLOR_LUZ_OFF) con borde oscuro
                l_obj = self.canvas.create_oval(cx - r_luz, cy - r_luz, cx + r_luz, cy + r_luz,
                                              fill=COLOR_LUZ_OFF, outline="#000", width=1)
                
                # Efecto de "brillo" vítreo estático (opcional, pequeño reflejo blanco)
                self.canvas.create_arc(cx - r_luz + 2, cy - r_luz + 2, cx + r_luz - 2, cy + r_luz - 2,
                                     start=135, extent=90, style=tk.ARC, outline="#ffffff", width=1, state="hidden") # Por ahora simple
                                     
                lights[color_key] = l_obj

            # Etiqueta de contador (Badge)
            txt_offset_y = -60 if k in ['N', 'E', 'O'] else 60
            if k in ['E', 'O']: txt_offset_y = -45
            
            # Fondo del texto
            padding_txt = 15
            txt_bg = self.canvas.create_rectangle(x-padding_txt, y+txt_offset_y-10, x+padding_txt, y+txt_offset_y+10,
                                                fill="#37474f", outline="#cfd8dc", width=1)
                                                
            txt = self.canvas.create_text(x, y+txt_offset_y, text=f"{k}: 0", 
                                        fill="white", font=("Roboto", 9, "bold"))
            
            # Guardamos referencias a todo
            self.sem_graficos[k] = {
                'body': body,
                'luz_roja': lights['red'],
                'luz_amarilla': lights['yellow'],
                'luz_verde': lights['green'],
                'txt': txt,
                'txt_bg': txt_bg
            }

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
                    from config import COLOR_LUZ_ROJA, COLOR_LUZ_AMARILLA, COLOR_LUZ_VERDE, COLOR_LUZ_OFF
                    from models import EstadoSemaforo
                    
                    _, id_sem, estado_val, num_autos = msg
                    
                    # Mapear estado a activación de luces
                    # Primero apagamos todas
                    self.canvas.itemconfig(self.sem_graficos[id_sem]['luz_roja'], fill=COLOR_LUZ_OFF)
                    self.canvas.itemconfig(self.sem_graficos[id_sem]['luz_amarilla'], fill=COLOR_LUZ_OFF)
                    self.canvas.itemconfig(self.sem_graficos[id_sem]['luz_verde'], fill=COLOR_LUZ_OFF)
                    
                    # Encendemos la correspondiente
                    if estado_val == EstadoSemaforo.ROJO.value:
                        self.canvas.itemconfig(self.sem_graficos[id_sem]['luz_roja'], fill=COLOR_LUZ_ROJA)
                    elif estado_val == EstadoSemaforo.AMARILLO.value:
                        self.canvas.itemconfig(self.sem_graficos[id_sem]['luz_amarilla'], fill=COLOR_LUZ_AMARILLA)
                    elif estado_val == EstadoSemaforo.VERDE.value:
                        self.canvas.itemconfig(self.sem_graficos[id_sem]['luz_verde'], fill=COLOR_LUZ_VERDE)
                        
                    self.canvas.itemconfig(self.sem_graficos[id_sem]['txt'], text=f"{id_sem}: {num_autos}")
                    
                    self.actualizar_cola_visual(id_sem, num_autos)
                    
                    # Asegurar que el semáforo completo esté encima
                    sg = self.sem_graficos[id_sem]
                    self.canvas.tag_raise(sg['body'])
                    self.canvas.tag_raise(sg['luz_roja'])
                    self.canvas.tag_raise(sg['luz_amarilla'])
                    self.canvas.tag_raise(sg['luz_verde'])
                    self.canvas.tag_raise(sg['txt_bg'])
                    self.canvas.tag_raise(sg['txt'])
                    
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
        
        # Asegurar que el semáforo completo esté encima
        sg = self.sem_graficos[id_sem]
        self.canvas.tag_raise(sg['body'])
        self.canvas.tag_raise(sg['luz_roja'])
        self.canvas.tag_raise(sg['luz_amarilla'])
        self.canvas.tag_raise(sg['luz_verde'])
        self.canvas.tag_raise(sg['txt_bg'])
        self.canvas.tag_raise(sg['txt'])

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
        
        # Asegurar que todos los semáforos siempre estén encima
        for sem_id, sg in self.sem_graficos.items():
            self.canvas.tag_raise(sg['body'])
            self.canvas.tag_raise(sg['luz_roja'])
            self.canvas.tag_raise(sg['luz_amarilla'])
            self.canvas.tag_raise(sg['luz_verde'])
            self.canvas.tag_raise(sg['txt_bg'])
            self.canvas.tag_raise(sg['txt'])
            
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
    
    def abrir_vistas(self):
        """Abre el panel de vistas de imágenes"""
        if self.vista_imagenes_panel is None or (self.vista_imagenes_panel.window is None or not self.vista_imagenes_panel.window.winfo_exists()):
            self.vista_imagenes_panel = VistaImagenes(self.root)
            self.vista_imagenes_panel.crear_ventana()
        else:
            # Si ya está abierto, traerlo al frente
            self.vista_imagenes_panel.window.lift()
            self.vista_imagenes_panel.window.focus_force()


# ==========================================
# PANEL DE VISTAS DE IMÁGENES
# ==========================================

class VistaImagenes:
    """Panel para visualizar diferentes vistas de la intersección"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.imagen_actual = None
        self.imagen_tk = None
        self.imagen_pil_original = None  # Imagen PIL original para zoom
        self.nivel_zoom = 1.0  # Nivel de zoom actual (1.0 = 100%)
        
        # Rutas de las imágenes
        # Obtener la ruta del directorio raíz del proyecto
        current_file = os.path.abspath(__file__)
        gui_dir = os.path.dirname(current_file)
        base_path = os.path.dirname(gui_dir)  # Subir un nivel desde gui/ al raíz
        
        images_dir = os.path.join(base_path, 'Images')
        self.rutas_imagenes = {
            'Norte': os.path.join(images_dir, 'Norte.png'),
            'Sur': os.path.join(images_dir, 'Sur.png'),
            'Este': os.path.join(images_dir, 'Este.png'),
            'Oeste': os.path.join(images_dir, 'Oeste.png'),
            'Aérea': os.path.join(images_dir, 'aerea.png')
        }
        
        # Vista actual
        self.vista_actual = 'Aérea'
    
    def crear_ventana(self):
        """Crea la ventana de vistas"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Vistas de la Intersección")
        self.window.geometry("1000x800")
        self.window.protocol("WM_DELETE_WINDOW", self.cerrar)
        
        # Header
        header = tk.Frame(self.window, bg="#2c3e50", pady=15)
        header.pack(fill=tk.X)
        
        titulo = tk.Label(header, text="🖼️ Vistas de la Intersección", 
                         font=("Arial", 16, "bold"), 
                         bg="#2c3e50", fg="white")
        titulo.pack()
        
        # Frame principal
        main_frame = tk.Frame(self.window, bg="#ecf0f1")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Frame para botones de selección
        btn_frame = tk.Frame(main_frame, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Crear botones para cada vista
        self.botones_vista = {}
        colores = {
            'Norte': '#3498db',
            'Sur': '#2ecc71',
            'Este': '#e74c3c',
            'Oeste': '#f39c12',
            'Aérea': '#9b59b6'
        }
        
        for vista in ['Norte', 'Sur', 'Este', 'Oeste', 'Aérea']:
            btn = tk.Button(btn_frame, text=vista,
                          font=("Arial", 10, "bold"),
                          bg=colores.get(vista, '#95a5a6'),
                          fg="white",
                          relief=tk.RAISED, bd=2,
                          width=12,
                          command=lambda v=vista: self.cambiar_vista(v))
            btn.pack(side=tk.LEFT, padx=5)
            self.botones_vista[vista] = btn
        
        # Frame para controles de zoom
        zoom_frame = tk.Frame(main_frame, bg="#ecf0f1")
        zoom_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Botón Zoom Out
        btn_zoom_out = tk.Button(zoom_frame, text="➖ Zoom Out",
                                font=("Arial", 9, "bold"),
                                bg="#e74c3c", fg="white",
                                relief=tk.RAISED, bd=2,
                                command=self.zoom_out)
        btn_zoom_out.pack(side=tk.LEFT, padx=5)
        
        # Botón Reset Zoom
        btn_zoom_reset = tk.Button(zoom_frame, text="🔄 Reset",
                                  font=("Arial", 9, "bold"),
                                  bg="#95a5a6", fg="white",
                                  relief=tk.RAISED, bd=2,
                                  command=self.zoom_reset)
        btn_zoom_reset.pack(side=tk.LEFT, padx=5)
        
        # Botón Zoom In
        btn_zoom_in = tk.Button(zoom_frame, text="➕ Zoom In",
                               font=("Arial", 9, "bold"),
                               bg="#2ecc71", fg="white",
                               relief=tk.RAISED, bd=2,
                               command=self.zoom_in)
        btn_zoom_in.pack(side=tk.LEFT, padx=5)
        
        # Label para mostrar nivel de zoom
        self.label_zoom = tk.Label(zoom_frame, text="Zoom: 100%",
                                  font=("Arial", 9),
                                  bg="#ecf0f1", fg="#2c3e50")
        self.label_zoom.pack(side=tk.LEFT, padx=15)
        
        # Frame para la imagen con scroll
        canvas_frame = tk.Frame(main_frame, bg="#ecf0f1")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas con scrollbars
        scrollbar_v = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        scrollbar_h = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        
        self.canvas = tk.Canvas(canvas_frame, 
                               bg="#ffffff",
                               yscrollcommand=scrollbar_v.set,
                               xscrollcommand=scrollbar_h.set)
        
        scrollbar_v.config(command=self.canvas.yview)
        scrollbar_h.config(command=self.canvas.xview)
        
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind eventos de rueda del mouse para zoom
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)  # Linux
        self.canvas.bind("<Button-5>", self.on_mousewheel)  # Linux
        self.canvas.focus_set()  # Permitir que el canvas reciba eventos
        
        # Cargar imagen inicial
        self.cargar_imagen(self.vista_actual)
    
    def cambiar_vista(self, vista):
        """Cambia a la vista seleccionada"""
        self.vista_actual = vista
        self.nivel_zoom = 1.0  # Resetear zoom al cambiar vista
        self.cargar_imagen(vista)
        
        # Actualizar apariencia de botones
        for nombre, btn in self.botones_vista.items():
            if nombre == vista:
                btn.config(relief=tk.SUNKEN, state=tk.DISABLED)
            else:
                btn.config(relief=tk.RAISED, state=tk.NORMAL)
    
    def cargar_imagen(self, vista):
        """Carga y muestra la imagen seleccionada"""
        ruta = self.rutas_imagenes.get(vista)
        
        if not ruta or not os.path.exists(ruta):
            # Mostrar mensaje de error
            self.canvas.delete("all")
            self.canvas.create_text(400, 300, 
                                   text=f"Imagen no encontrada: {ruta}",
                                   font=("Arial", 12),
                                   fill="#e74c3c")
            return
        
        try:
            if PIL_DISPONIBLE:
                # Cargar imagen con PIL (mejor calidad y redimensionamiento)
                self.imagen_pil_original = Image.open(ruta)
                
                # Aplicar zoom inicial
                self.aplicar_zoom()
            else:
                # Usar tkinter directamente (sin redimensionamiento ni zoom)
                self.imagen_tk = tk.PhotoImage(file=ruta)
                self.imagen_pil_original = None
                self.mostrar_imagen()
            
        except Exception as e:
            # Mostrar error
            self.canvas.delete("all")
            error_msg = f"Error al cargar imagen:\n{str(e)}"
            if not PIL_DISPONIBLE:
                error_msg += "\n\nNota: Se recomienda instalar Pillow para mejor soporte de imágenes:\npip install Pillow"
            self.canvas.create_text(400, 300, 
                                   text=error_msg,
                                   font=("Arial", 12),
                                   fill="#e74c3c",
                                   justify=tk.CENTER)
    
    def aplicar_zoom(self):
        """Aplica el nivel de zoom actual a la imagen"""
        if not PIL_DISPONIBLE or not self.imagen_pil_original:
            return
        
        # Obtener tamaño original
        ancho_original, alto_original = self.imagen_pil_original.size
        
        # Calcular nuevo tamaño con zoom
        nuevo_ancho = int(ancho_original * self.nivel_zoom)
        nuevo_alto = int(alto_original * self.nivel_zoom)
        
        # Redimensionar imagen
        imagen_redimensionada = self.imagen_pil_original.resize(
            (nuevo_ancho, nuevo_alto), 
            Image.Resampling.LANCZOS
        )
        
        # Convertir a PhotoImage
        self.imagen_tk = ImageTk.PhotoImage(imagen_redimensionada)
        
        # Mostrar imagen
        self.mostrar_imagen()
    
    def mostrar_imagen(self):
        """Muestra la imagen actual en el canvas"""
        if not self.imagen_tk:
            return
        
        # Limpiar canvas
        self.canvas.delete("all")
        
        # Mostrar imagen centrada
        x = max(400, self.imagen_tk.width() // 2 + 10)
        y = max(350, self.imagen_tk.height() // 2 + 10)
        
        self.canvas.create_image(x, y, image=self.imagen_tk, anchor=tk.CENTER)
        
        # Configurar scroll region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        # Guardar referencia para evitar garbage collection
        self.imagen_actual = self.imagen_tk
        
        # Actualizar label de zoom
        self.actualizar_label_zoom()
    
    def zoom_in(self):
        """Aumenta el nivel de zoom"""
        if self.nivel_zoom < 5.0:  # Límite máximo de 500%
            self.nivel_zoom = min(5.0, self.nivel_zoom * 1.2)
            if PIL_DISPONIBLE and self.imagen_pil_original:
                self.aplicar_zoom()
            else:
                self.actualizar_label_zoom()
    
    def zoom_out(self):
        """Disminuye el nivel de zoom"""
        if self.nivel_zoom > 0.1:  # Límite mínimo de 10%
            self.nivel_zoom = max(0.1, self.nivel_zoom / 1.2)
            if PIL_DISPONIBLE and self.imagen_pil_original:
                self.aplicar_zoom()
            else:
                self.actualizar_label_zoom()
    
    def zoom_reset(self):
        """Resetea el zoom a 100%"""
        self.nivel_zoom = 1.0
        if PIL_DISPONIBLE and self.imagen_pil_original:
            self.aplicar_zoom()
        else:
            self.actualizar_label_zoom()
    
    def on_mousewheel(self, event):
        """Maneja el evento de rueda del mouse para zoom"""
        if event.delta > 0 or event.num == 4:  # Scroll hacia arriba
            self.zoom_in()
        elif event.delta < 0 or event.num == 5:  # Scroll hacia abajo
            self.zoom_out()
    
    def actualizar_label_zoom(self):
        """Actualiza el label que muestra el nivel de zoom"""
        if self.label_zoom:
            porcentaje = int(self.nivel_zoom * 100)
            self.label_zoom.config(text=f"Zoom: {porcentaje}%")
    
    def cerrar(self):
        """Cierra la ventana de vistas"""
        if self.window:
            self.window.destroy()
            self.window = None

