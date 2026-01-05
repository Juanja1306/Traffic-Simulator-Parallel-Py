import tkinter as tk
from tkinter import messagebox
from config import (
    ANCHO_VENTANA, ALTO_VENTANA, COLOR_FONDO, COLOR_CALLE, COLOR_LINEA,
    COLOR_AUTO_ESPERA, COLOR_AUTO_CRUZANDO, CENTRO_X, CENTRO_Y,
    ANCHO_CALLE, OFFSET_SEMAFORO
)
from models import Estadisticas
from utils import obtener_info_sistema
from gui.monitor import MonitorPanel

# ==========================================
# GUI CON ANIMACIÓN DE AUTOS
# ==========================================

class TrafficApp:
    def __init__(self, root, cola_comunicacion, modo=None, workers=None):
        self.root = root
        self.cola = cola_comunicacion
        self.modo = modo
        self.workers = workers or []
        self.root.title("Simulador de Tráfico Paralelo - UPS Cuenca")
        self.root.geometry("900x700")
        
        self.info_sys = obtener_info_sistema(modo, self.workers)
        self.stats = Estadisticas()
        
        # Estructuras para animación
        self.autos_animados = [] # Lista de autos moviéndose actualmente
        self.colas_graficas = {'N': [], 'S': [], 'E': [], 'O': []} # IDs de rectángulos en espera
        
        # Panel de monitoreo
        self.monitor_panel = None
        
        self.setup_ui()
        self.running = True
        
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
        
        # Botón para abrir monitoreo
        btn_monitor = tk.Button(header_content, text="📊 Monitoreo", 
                               font=("Arial", 9, "bold"),
                               bg="#3498db", fg="white",
                               relief=tk.RAISED, bd=2,
                               command=self.abrir_monitoreo)
        btn_monitor.pack(side=tk.RIGHT, padx=5)

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
            self.canvas.move(auto['id'], auto['vx'], auto['vy'])
            coords = self.canvas.coords(auto['id'])
            
            # Verificar si salió de la pantalla
            if (coords[2] < 0 or coords[0] > ANCHO_VENTANA or 
                coords[3] < 0 or coords[1] > ALTO_VENTANA):
                por_eliminar.append(auto)
        
        # Limpieza
        for auto in por_eliminar:
            self.canvas.delete(auto['id'])
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

