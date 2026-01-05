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
import platform
import multiprocessing

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
        # Importar tema y configuración nueva
        from config import (THEME_BG, THEME_BG_SEC, THEME_FG, THEME_FG_SEC, THEME_ACCENT, 
                          THEME_BORDER, CANVAS_ANCHO, CANVAS_ALTO, COLOR_SEMAFORO_CUERPO, 
                          COLOR_LUZ_OFF, COLOR_LUZ_ROJA)
        
        self.root.configure(bg=THEME_BG)
        # Centrar ventana en pantalla obligatoriamente
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_c = int((screen_width/2) - (ANCHO_VENTANA/2))
        y_c = int((screen_height/2) - (ALTO_VENTANA/2))
        self.root.geometry(f"{ANCHO_VENTANA}x{ALTO_VENTANA}+{x_c}+{y_c}")
        self.root.resizable(False, False)

        # ==========================================
        # LAYOUT PRINCIPAL (2 COLUMNAS)
        # ==========================================
        main_container = tk.Frame(self.root, bg=THEME_BG)
        main_container.pack(fill=tk.BOTH, expand=True)

        # ------------------------------------------
        # COLUMNA IZQUIERDA: SIMULACIÓN (Canvas)
        # ------------------------------------------
        sim_frame = tk.Frame(main_container, bg=THEME_BG, width=CANVAS_ANCHO, height=CANVAS_ALTO)
        sim_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sim_frame.pack_propagate(False)

        # Canvas Principal
        self.canvas = tk.Canvas(sim_frame, width=CANVAS_ANCHO, height=CANVAS_ALTO, 
                              bg=COLOR_FONDO, highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        self.dibujar_calles()
        
        # ------------------------------------------
        # COLUMNA DERECHA: SIDEBAR (Panel de Control)
        # ------------------------------------------
        sidebar = tk.Frame(main_container, bg=THEME_BG_SEC, width=(ANCHO_VENTANA - CANVAS_ANCHO))
        sidebar.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        sidebar.pack_propagate(False) 
        
        # Borde decorativo
        tk.Frame(sidebar, bg=THEME_BORDER, width=2).pack(side=tk.LEFT, fill=tk.Y)
        
        # Contenido Sidebar
        side_content = tk.Frame(sidebar, bg=THEME_BG_SEC, padx=20, pady=25)
        side_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 1. Título
        tk.Label(side_content, text="TRAFFIC\nCONTROLLER", justify=tk.LEFT,
                font=("Segoe UI", 20, "bold"), bg=THEME_BG_SEC, fg=THEME_FG).pack(anchor="w", pady=(0, 20))

        # 2. Info Sistema Expandida (Host Specs)
        import platform
        
        info_card = tk.LabelFrame(side_content, text=" HOST SPECS ", font=("Segoe UI", 9, "bold"),
                                bg=THEME_BG_SEC, fg=THEME_FG_SEC, bd=1, relief=tk.SOLID)
        info_card.pack(fill=tk.X, pady=(0, 20), ipady=5)
        
        def add_info_row(parent, label, value, color_val=THEME_ACCENT):
            row = tk.Frame(parent, bg=THEME_BG_SEC, pady=1)
            row.pack(fill=tk.X, padx=10)
            tk.Label(row, text=label, font=("Segoe UI", 8), bg=THEME_BG_SEC, fg=THEME_FG_SEC).pack(side=tk.LEFT)
            tk.Label(row, text=value, font=("Segoe UI", 8, "bold"), bg=THEME_BG_SEC, fg=color_val).pack(side=tk.RIGHT)

        # Obtener datos reales del Host (Linux)
        uname = platform.uname()
        cpu_model = "Unknown"
        ram_total = "Unknown"
        
        try:
            # Obtener Modelo de CPU detallado
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        cpu_model = line.split(":")[1].strip()
                        # Limpiar un poco el string si es muy largo
                        cpu_model = cpu_model.replace("Intel(R) Core(TM) ", "")
                        cpu_model = cpu_model.replace("CPU @", "@")
                        break
            
            # Obtener RAM Total
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if "MemTotal" in line:
                        # Formato: MemTotal:        16316548 kB
                        parts = line.split()
                        kb_val = int(parts[1])
                        gb_val = kb_val / (1024 * 1024)
                        ram_total = f"{gb_val:.1f} GB"
                        break
        except:
            # Fallback simple si no estamos en Linux o falla lectura
            cpu_model = platform.machine()
            ram_total = "N/A"

        cores = multiprocessing.cpu_count()
        
        # Mostrar datos en el Sidebar
        add_info_row(info_card, "OS:", uname.system)
        add_info_row(info_card, "CPU:", cpu_model) # Modelo exacto
        add_info_row(info_card, "RAM:", ram_total) # RAM Dinámica
        add_info_row(info_card, "Cores:", str(cores))
        add_info_row(info_card, "Mode:", self.info_sys['modo'], "#00E676")
        add_info_row(info_card, "GIL:", "OFF" if "Free" in self.info_sys['gil_status'] else "ON", 
                     "#10b981" if "Free" in self.info_sys['gil_status'] else "#f59e0b")

        # 3. KPIs
        stats_frame = tk.Frame(side_content, bg=THEME_BG_SEC)
        stats_frame.pack(fill=tk.X, pady=(0, 30))
        tk.Label(stats_frame, text="LIVE STATISTICS", font=("Segoe UI", 8, "bold"), bg=THEME_BG_SEC, fg=THEME_FG_SEC).pack(anchor="w", pady=(0, 5))
        
        self.sv_kpi_autos = tk.StringVar(value="0")
        self.sv_kpi_tiempo = tk.StringVar(value="0.0s")
        
        def create_kpi(parent, title, var):
            f = tk.Frame(parent, bg="#1e293b", padx=10, pady=10)
            f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
            tk.Label(f, text=title, font=("Segoe UI", 8), bg="#1e293b", fg=THEME_FG_SEC).pack(anchor="w")
            tk.Label(f, textvariable=var, font=("Segoe UI", 18, "bold"), bg="#1e293b", fg=THEME_FG).pack(anchor="w")
        
        grid_stats = tk.Frame(stats_frame, bg=THEME_BG_SEC)
        grid_stats.pack(fill=tk.X)
        create_kpi(grid_stats, "VEHICLES", self.sv_kpi_autos)
        create_kpi(grid_stats, "WAIT TIME", self.sv_kpi_tiempo)

        # 4. Controls (Iconos ASCII)
        tk.Label(side_content, text="CONTROLS", font=("Segoe UI", 8, "bold"), bg=THEME_BG_SEC, fg=THEME_FG_SEC).pack(anchor="w", pady=(0, 10))
        
        def crear_boton_sidebar(parent, text, bg_color, cmd, icon=""):
            # Icon ahora es texto plano seguro
            btn = tk.Button(parent, text=f"{icon} {text}", font=("Segoe UI", 10, "bold"),
                           bg=bg_color, fg="white", activebackground="white", activeforeground=bg_color,
                           relief=tk.FLAT, bd=0, cursor="hand2", height=2, command=cmd)
            btn.pack(fill=tk.X, pady=5)
            # Hover
            def on_enter(e): btn['bg'] = "#334155" if bg_color == THEME_BG_SEC else "#ffffff"; btn['fg'] = bg_color if bg_color != THEME_BG_SEC else "white"
            def on_leave(e): btn['bg'] = bg_color; btn['fg'] = "white"
            btn.bind("<Enter>", on_enter); btn.bind("<Leave>", on_leave)
            return btn

        crear_boton_sidebar(side_content, "MONITOR PANEL", "#0ea5e9", self.abrir_monitoreo, "[M]")
        crear_boton_sidebar(side_content, "CAMERA VIEWS", "#8b5cf6", self.abrir_vistas, "[O]")
        self.btn_ambulancia = crear_boton_sidebar(side_content, "DISPATCH AMBULANCE", "#f59e0b", self.activar_ambulancia, "(+)")
        tk.Frame(side_content, bg=THEME_BG_SEC).pack(fill=tk.BOTH, expand=True) # Spacer
        crear_boton_sidebar(side_content, "EXIT SIMULATION", "#ef4444", self.volver_atras, "[X]")

        # ------------------------------------------
        # SEMÁFOROS (Lógica Visual)
        # ------------------------------------------
        self.sem_graficos = {}
        offset_visual = OFFSET_SEMAFORO + 15
        coords_sem = {'N': (CENTRO_X, CENTRO_Y - offset_visual), 'S': (CENTRO_X, CENTRO_Y + offset_visual),
                      'E': (CENTRO_X + offset_visual, CENTRO_Y), 'O': (CENTRO_X - offset_visual, CENTRO_Y)}
        
        for k, (x, y) in coords_sem.items():
            is_vertical = k in ['N', 'S']
            w_body, h_body = (34, 90) if is_vertical else (90, 34)
            x1, y1 = x - w_body/2, y - h_body/2
            x2, y2 = x + w_body/2, y + h_body/2
            
            body = self.canvas.create_rectangle(x1, y1, x2, y2, fill="#1a1a1a", outline="#444", width=2)
            
            r_luz, spacing = 11, 28
            positions = {'red': (0, -spacing), 'yellow': (0, 0), 'green': (0, spacing)} if is_vertical else \
                        {'red': (-spacing, 0), 'yellow': (0, 0), 'green': (spacing, 0)}
            
            lights = {}
            for color_key, (dx, dy) in positions.items():
                cx, cy = x + dx, y + dy
                l_obj = self.canvas.create_oval(cx - r_luz, cy - r_luz, cx + r_luz, cy + r_luz, fill=COLOR_LUZ_OFF, outline="#000", width=1)
                self.canvas.create_arc(cx - r_luz + 2, cy - r_luz + 2, cx + r_luz - 2, cy + r_luz - 2, start=135, extent=90, style=tk.ARC, outline="#ffffff", width=1, state="hidden")
                lights[color_key] = l_obj

            txt_offset_y = -60 if k in ['N', 'E', 'O'] else 60
            if k in ['E', 'O']: txt_offset_y = -45
            padding_txt = 15
            txt_bg = self.canvas.create_rectangle(x-padding_txt, y+txt_offset_y-10, x+padding_txt, y+txt_offset_y+10, fill="#37474f", outline="#cfd8dc", width=1)
            txt = self.canvas.create_text(x, y+txt_offset_y, text=f"{k}: 0", fill="white", font=("Roboto", 9, "bold"))
            
            self.sem_graficos[k] = {'body': body, 'luz_roja': lights['red'], 'luz_amarilla': lights['yellow'], 
                                  'luz_verde': lights['green'], 'txt': txt, 'txt_bg': txt_bg}

    def dibujar_calles(self):
        # Calles (Usan COLOR_CALLE actualizado = asfalto azulado)
        self.canvas.create_rectangle(CENTRO_X - ANCHO_CALLE/2, 0, CENTRO_X + ANCHO_CALLE/2, ALTO_VENTANA, fill=COLOR_CALLE, outline="")
        self.canvas.create_rectangle(0, CENTRO_Y - ANCHO_CALLE/2, ANCHO_VENTANA, CENTRO_Y + ANCHO_CALLE/2, fill=COLOR_CALLE, outline="")
        
        # Líneas centrales (Amarillo Neón)
        self.canvas.create_line(CENTRO_X, 0, CENTRO_X, ALTO_VENTANA, fill=COLOR_LINEA, width=2, dash=(20, 20))
        self.canvas.create_line(0, CENTRO_Y, ANCHO_VENTANA, CENTRO_Y, fill=COLOR_LINEA, width=2, dash=(20, 20))
        
        # Líneas de parada (Stop lines - Blanco brillante)
        stop_offset = ANCHO_CALLE/2 + 10
        # Norte
        self.canvas.create_line(CENTRO_X, CENTRO_Y - stop_offset, CENTRO_X - ANCHO_CALLE/2, CENTRO_Y - stop_offset, fill="#ffffff", width=4)
        # Sur
        self.canvas.create_line(CENTRO_X, CENTRO_Y + stop_offset, CENTRO_X + ANCHO_CALLE/2, CENTRO_Y + stop_offset, fill="#ffffff", width=4)
        # Este
        self.canvas.create_line(CENTRO_X + stop_offset, CENTRO_Y, CENTRO_X + stop_offset, CENTRO_Y - ANCHO_CALLE/2, fill="#ffffff", width=4)
        # Oeste
        self.canvas.create_line(CENTRO_X - stop_offset, CENTRO_Y, CENTRO_X - stop_offset, CENTRO_Y + ANCHO_CALLE/2, fill="#ffffff", width=4)

    def crear_vehiculo_visual(self, x, y, w, h, color, direccion, tag):
        """
        Dibuja un vehículo detallado (estilo Top-Down) y agrupa los elementos bajo un tag.
        Dirección: 'N' (mira abajo), 'S' (mira arriba), 'E' (mira izq), 'O' (mira der)
        Nota: La dirección es hacia dónde apunta el frente del auto.
        """
        # Coordenadas bounding box
        x1, y1 = x - w/2, y - h/2
        x2, y2 = x + w/2, y + h/2
        
        # 1. Sombra (pequeño offset)
        # Tkinter no soporta HEX con Alpha (#RRGGBBAA). Usamos un gris oscuro sólido para simular sombra.
        self.canvas.create_oval(x1+2, y1+2, x2+2, y2+2, fill="#1a1a1a", outline="", tags=tag)
        # Mejor usamos stipple para semi-transparencia si fuera necesario, pero gris oscuro plano (sombra sólida) está bien para estilo flat
        self.canvas.create_rectangle(x1+3, y1+3, x2+3, y2+3, fill="#111", outline="", tags=tag) # Sombra simple
        
        # 2. Carrocería
        # Usamos polygon para esquinas redondeadas simuladas o simplemente rect
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#2c3e50", width=1, tags=tag)
        
        # Colores de detalles
        glass_color = "#34495e" # Vidrios oscuros
        headlight_color = "#f1c40f" # Faros amarillos
        taillight_color = "#e74c3c" # Luces rojas
        
        # 3. Detalles según orientación
        if direccion in ['N', 'S']: # Vertical
            # Techo (Roof) - simula parabrisas y luneta trasera dejando huecos
            roof_margin_y = h * 0.25
            roof_margin_x = 2
            self.canvas.create_rectangle(x1+roof_margin_x, y1+roof_margin_y, x2-roof_margin_x, y2-roof_margin_y, 
                                       fill=color, outline=glass_color, width=2, tags=tag)
            
            # Faros
            fw, fh = 4, 3 # Dimensión faros
            if direccion == 'N': # Mira ABAJO
                # Delanteros (Abajo)
                self.canvas.create_rectangle(x1+2, y2-fh, x1+2+fw, y2, fill=headlight_color, outline="", tags=tag)
                self.canvas.create_rectangle(x2-2-fw, y2-fh, x2-2, y2, fill=headlight_color, outline="", tags=tag)
                # Traseros (Arriba)
                self.canvas.create_rectangle(x1+2, y1, x1+2+fw, y1+fh, fill=taillight_color, outline="", tags=tag)
                self.canvas.create_rectangle(x2-2-fw, y1, x2-2, y1+fh, fill=taillight_color, outline="", tags=tag)
            else: # Mira ARRIBA
                # Delanteros (Arriba)
                self.canvas.create_rectangle(x1+2, y1, x1+2+fw, y1+fh, fill=headlight_color, outline="", tags=tag)
                self.canvas.create_rectangle(x2-2-fw, y1, x2-2, y1+fh, fill=headlight_color, outline="", tags=tag)
                # Traseros (Abajo)
                self.canvas.create_rectangle(x1+2, y2-fh, x1+2+fw, y2, fill=taillight_color, outline="", tags=tag)
                self.canvas.create_rectangle(x2-2-fw, y2-fh, x2-2, y2, fill=taillight_color, outline="", tags=tag)
                
        else: # Horizontal
            # Techo
            roof_margin_x = w * 0.25
            roof_margin_y = 2
            self.canvas.create_rectangle(x1+roof_margin_x, y1+roof_margin_y, x2-roof_margin_x, y2-roof_margin_y, 
                                       fill=color, outline=glass_color, width=2, tags=tag)
            
            # Faros
            fw, fh = 3, 4
            if direccion == 'E': # Mira IZQUIERDA (<--)
                # Delanteros (Izq)
                self.canvas.create_rectangle(x1, y1+2, x1+fw, y1+2+fh, fill=headlight_color, outline="", tags=tag)
                self.canvas.create_rectangle(x1, y2-2-fh, x1+fw, y2-2, fill=headlight_color, outline="", tags=tag)
                # Traseros (Der)
                self.canvas.create_rectangle(x2-fw, y1+2, x2, y1+2+fh, fill=taillight_color, outline="", tags=tag)
                self.canvas.create_rectangle(x2-fw, y2-2-fh, x2, y2-2, fill=taillight_color, outline="", tags=tag)
            else: # Mira DERECHA (-->)
                # Delanteros (Der)
                self.canvas.create_rectangle(x2-fw, y1+2, x2, y1+2+fh, fill=headlight_color, outline="", tags=tag)
                self.canvas.create_rectangle(x2-fw, y2-2-fh, x2, y2-2, fill=headlight_color, outline="", tags=tag)
                # Traseros (Izq)
                self.canvas.create_rectangle(x1, y1+2, x1+fw, y1+2+fh, fill=taillight_color, outline="", tags=tag)
                self.canvas.create_rectangle(x1, y2-2-fh, x1+fw, y2-2, fill=taillight_color, outline="", tags=tag)

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
                    prom = self.stats.tiempo_total_espera / self.stats.total_vehiculos if self.stats.total_vehiculos > 0 else 0
                    
                    # Actualizar KPIs del Sidebar
                    self.sv_kpi_autos.set(f"{self.stats.total_vehiculos}")
                    self.sv_kpi_tiempo.set(f"{prom:.1f}s")
                    # self.lbl_stats.config(text=...) # Eliminado (Label antiguo)

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
        for tag in self.colas_graficas[id_sem]:
            self.canvas.delete(tag)
        self.colas_graficas[id_sem] = []
        
        # Parámetros de dibujo
        w_auto, h_auto = 22, 36  # Un poco más grandes y proporcionales
        gap = 8
        stop_dist = ANCHO_CALLE/2 + 15
        
        # Limitar visualización a 10 autos para no saturar
        cantidad_visible = min(cantidad, 12)
        
        for i in range(cantidad_visible):
            tag = f"cola_{id_sem}_{i}" # Tag único para este auto
            
            if id_sem == 'N': # Cola hacia arriba, miran hacia ABAJO ('N')
                x = CENTRO_X - ANCHO_CALLE/4
                y = (CENTRO_Y - stop_dist) - (i * (h_auto + gap)) - h_auto/2
                self.crear_vehiculo_visual(x, y, w_auto, h_auto, COLOR_AUTO_ESPERA, 'N', tag)
                
            elif id_sem == 'S': # Cola hacia abajo, miran hacia ARRIBA ('S')
                x = CENTRO_X + ANCHO_CALLE/4
                y = (CENTRO_Y + stop_dist) + (i * (h_auto + gap)) + h_auto/2
                self.crear_vehiculo_visual(x, y, w_auto, h_auto, COLOR_AUTO_ESPERA, 'S', tag)
                
            elif id_sem == 'E': # Cola hacia derecha, miran hacia IZQUIERDA ('E')
                # Nota: Intercambiamos w y h para coches horizontales
                x = (CENTRO_X + stop_dist) + (i * (w_auto + gap)) + w_auto/2 # w_auto es el largo aquí
                y = CENTRO_Y - ANCHO_CALLE/4
                self.crear_vehiculo_visual(x, y, h_auto, w_auto, COLOR_AUTO_ESPERA, 'E', tag) # w=36, h=22
                
            elif id_sem == 'O': # Cola hacia izquierda, miran hacia DERECHA ('O')
                x = (CENTRO_X - stop_dist) - (i * (w_auto + gap)) - w_auto/2
                y = CENTRO_Y + ANCHO_CALLE/4
                self.crear_vehiculo_visual(x, y, h_auto, w_auto, COLOR_AUTO_ESPERA, 'O', tag)
            
            self.colas_graficas[id_sem].append(tag)
        
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
        w, h = 22, 36
        vx, vy = 0, 0
        import time
        tag = f"mov_{id_sem}_{int(time.time()*1000)}" # Tag único con timestamp
        
        # Determinar posición inicial y velocidad según dirección
        if id_sem == 'N': # Baja, mira ABAJO
            x = CENTRO_X - ANCHO_CALLE/4
            y = CENTRO_Y - ANCHO_CALLE/2 - 20
            vx, vy = 0, 8
            self.crear_vehiculo_visual(x, y, w, h, COLOR_AUTO_CRUZANDO, 'N', tag)
            
        elif id_sem == 'S': # Sube, mira ARRIBA
            x = CENTRO_X + ANCHO_CALLE/4
            y = CENTRO_Y + ANCHO_CALLE/2 + 20
            vx, vy = 0, -8
            self.crear_vehiculo_visual(x, y, w, h, COLOR_AUTO_CRUZANDO, 'S', tag)
            
        elif id_sem == 'E': # Va a izquierda, mira IZQUIERDA
            x = CENTRO_X + ANCHO_CALLE/2 + 20
            y = CENTRO_Y - ANCHO_CALLE/4
            vx, vy = -8, 0
            self.crear_vehiculo_visual(x, y, h, w, COLOR_AUTO_CRUZANDO, 'E', tag)
            
        elif id_sem == 'O': # Va a derecha, mira DERECHA
            x = CENTRO_X - ANCHO_CALLE/2 - 20
            y = CENTRO_Y + ANCHO_CALLE/4
            vx, vy = 8, 0
            self.crear_vehiculo_visual(x, y, h, w, COLOR_AUTO_CRUZANDO, 'O', tag)
            
        self.autos_animados.append({'tag': tag, 'vx': vx, 'vy': vy}) # Guardamos el TAG


    def bucle_animacion(self):
        """Actualiza la posición de los autos animados"""
        por_eliminar = []
        
        for auto in self.autos_animados:
            # Mover TODO el grupo asociado al tag
            self.canvas.move(auto['tag'], auto['vx'], auto['vy'])
            
            # Si es ambulancia, mover también el texto (aunque ahora la ambulancia puede usar tags grupo si la actualizamos)
            if 'texto' in auto:
                self.canvas.move(auto['texto'], auto['vx'], auto['vy'])
            
            # Obtener coords del bounding box del grupo
            coords = self.canvas.bbox(auto['tag'])
            
            # Verificar si salió de la pantalla
            if not coords or (coords[2] < 0 or coords[0] > ANCHO_VENTANA or 
                              coords[3] < 0 or coords[1] > ALTO_VENTANA):
                por_eliminar.append(auto)
        
        # Limpieza
        for auto in por_eliminar:
            self.canvas.delete(auto['tag']) # Borra todo el grupo
            if 'texto' in auto:  # Si es ambulancia antigua
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
        w, h = 25, 38  # Ambulancia más grande
        vx, vy = 0, 0
        import time
        tag = f"amb_{id_sem}_{int(time.time()*1000)}"
        
        # Determinar posición inicial y velocidad según dirección
        if id_sem == 'N': # Baja
            x = CENTRO_X - ANCHO_CALLE/4
            y = CENTRO_Y - ANCHO_CALLE/2 - 20
            vx, vy = 0, 10  # Más rápida
            self.crear_vehiculo_visual(x, y, w, h, COLOR_AMBULANCIA, 'N', tag)
        elif id_sem == 'S': # Sube
            x = CENTRO_X + ANCHO_CALLE/4
            y = CENTRO_Y + ANCHO_CALLE/2 + 20
            vx, vy = 0, -10
            self.crear_vehiculo_visual(x, y, w, h, COLOR_AMBULANCIA, 'S', tag)
        elif id_sem == 'E': # Va a izquierda
            x = CENTRO_X + ANCHO_CALLE/2 + 20
            y = CENTRO_Y - ANCHO_CALLE/4
            vx, vy = -10, 0
            self.crear_vehiculo_visual(x, y, h, w, COLOR_AMBULANCIA, 'E', tag)
        elif id_sem == 'O': # Va a derecha
            x = CENTRO_X - ANCHO_CALLE/2 - 20
            y = CENTRO_Y + ANCHO_CALLE/4
            vx, vy = 10, 0
            self.crear_vehiculo_visual(x, y, h, w, COLOR_AMBULANCIA, 'O', tag)
        
        # Añadir texto "AMB" sobre la ambulancia (como parte del mismo grupo visual)
        # Bbox para centrar texto
        coords = self.canvas.bbox(tag)
        if coords:
            cx = (coords[0] + coords[2]) / 2
            cy = (coords[1] + coords[3]) / 2
            self.canvas.create_text(cx, cy, text="AMB", fill="white", font=("Arial", 8, "bold"), tags=tag)
            
            # Cruz roja distintiva en el techo
            r_cross = 6
            self.canvas.create_line(cx-r_cross, cy, cx+r_cross, cy, fill="red", width=3, tags=tag)
            self.canvas.create_line(cx, cy-r_cross, cx, cy+r_cross, fill="red", width=3, tags=tag)
        
        self.autos_animados.append({'tag': tag, 'vx': vx, 'vy': vy, 'es_ambulancia': True})
    
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
        """Crea la ventana de vistas estilo Cyber-Dashboard"""
        from config import THEME_BG, THEME_BG_SEC, THEME_FG, THEME_FG_SEC, THEME_ACCENT, THEME_BORDER
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("Camera Views - Intersection Analysis")
        self.window.geometry("1100x850")
        self.window.configure(bg=THEME_BG)
        self.window.protocol("WM_DELETE_WINDOW", self.cerrar)
        
        # Container principal
        main_container = tk.Frame(self.window, bg=THEME_BG, padx=20, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Header limpio
        header = tk.Frame(main_container, bg=THEME_BG)
        header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header, text="CAMERA FEEDS", font=("Segoe UI", 20, "bold"), 
                bg=THEME_BG, fg=THEME_FG).pack(anchor="w")
        tk.Label(header, text="Real-time optical sensors visualization", font=("Segoe UI", 10), 
                bg=THEME_BG, fg=THEME_FG_SEC).pack(anchor="w")
        
        # Toolbar (Vistas + Zoom)
        toolbar = tk.Frame(main_container, bg=THEME_BG_SEC, padx=10, pady=10)
        toolbar.pack(fill=tk.X, pady=(0, 15))
        
        # 1. Botones de Vistas
        views_frame = tk.Frame(toolbar, bg=THEME_BG_SEC)
        views_frame.pack(side=tk.LEFT)
        
        self.botones_vista = {}
        # Colores Cyber para direcciones
        colores = {
            'Norte': '#3b82f6', # Azul
            'Sur': '#10b981',   # Verde
            'Este': '#ef4444',  # Rojo
            'Oeste': '#f59e0b', # Naranja
            'Aérea': '#8b5cf6'  # Violeta
        }
        
        def crear_tab(parent, text, color, cmd):
            # Botón plano que se ilumina al estar activo
            btn = tk.Button(parent, text=text,
                           font=("Segoe UI", 10, "bold"),
                           bg=THEME_BG, fg=THEME_FG_SEC, # Estado inactivo por defecto
                           activebackground=color, activeforeground="white",
                           relief=tk.FLAT, bd=0, cursor="hand2",
                           width=10, pady=5,
                           command=cmd)
            btn.pack(side=tk.LEFT, padx=2)
            
            # Guardamos el color original para efectos
            btn.color_activo = color 
            return btn

        for vista in ['Norte', 'Sur', 'Este', 'Oeste', 'Aérea']:
            btn = crear_tab(views_frame, vista, colores.get(vista, THEME_FG), 
                           lambda v=vista: self.cambiar_vista(v))
            self.botones_vista[vista] = btn

        # Separador
        tk.Frame(toolbar, bg=THEME_BORDER, width=2, height=30).pack(side=tk.LEFT, padx=15, fill=tk.Y)
        
        # 2. Controles de Zoom
        zoom_frame = tk.Frame(toolbar, bg=THEME_BG_SEC)
        zoom_frame.pack(side=tk.LEFT, padx=30)
        
        tk.Label(zoom_frame, text="ZOOM:", font=("Segoe UI", 9, "bold"), 
                bg=THEME_BG_SEC, fg=THEME_FG_SEC).pack(side=tk.LEFT, padx=(0, 10))
        
        def crear_zoom_btn(txt, cmd, w=4):
            b = tk.Button(zoom_frame, text=txt, font=("Segoe UI", 11, "bold"),
                         bg=THEME_BG_SEC, fg=THEME_FG,
                         activebackground=THEME_BG, activeforeground=THEME_FG,
                         relief=tk.FLAT, bd=0, cursor="hand2",
                         width=w, pady=2,
                         command=cmd)
            b.pack(side=tk.LEFT, padx=2)
            b.bind("<Enter>", lambda e: b.config(bg=THEME_BG))
            b.bind("<Leave>", lambda e: b.config(bg=THEME_BG_SEC))
            return b

        crear_zoom_btn("-", self.zoom_out)
        
        # Label directo con ancho fijo suficiente y sin containers extraños
        self.label_zoom = tk.Label(zoom_frame, text="100%", width=8,
                                  font=("Segoe UI", 11, "bold"),
                                  bg="#1e293b", fg=THEME_ACCENT)
        self.label_zoom.pack(side=tk.LEFT, padx=5, ipady=3) # ipady para altura
        
        crear_zoom_btn("+", self.zoom_in)
        
        # Botón Reset con ancho explícito para que no se colapse
        crear_zoom_btn("Reset", self.zoom_reset, w=6)

        # Frame para la imagen (Canvas container)
        # Usamos bg oscuro para enmarcar la imagen
        canvas_container = tk.Frame(main_container, bg="#000000", bd=2, relief=tk.SOLID) 
        # Borde #000 para contraste máximo con imagen
        canvas_container.pack(fill=tk.BOTH, expand=True)

        # Canvas con scrollbars (estilizados es difícil en tk standard, los dejamos default o minimizamos)
        scrollbar_v = tk.Scrollbar(canvas_container, orient=tk.VERTICAL)
        scrollbar_h = tk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
        
        self.canvas = tk.Canvas(canvas_container, 
                               bg="#0f172a", # Fondo del canvas (si la imagen es chica se ve esto)
                               highlightthickness=0,
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
        self.canvas.focus_set()
        
        # Cargar imagen inicial
        self.cargar_imagen(self.vista_actual)
    
    def cambiar_vista(self, vista):
        """Cambia a la vista seleccionada (Cyber Style)"""
        from config import THEME_BG, THEME_FG_SEC
        
        self.vista_actual = vista
        self.nivel_zoom = 1.0  # Resetear zoom al cambiar vista
        self.cargar_imagen(vista)
        
        # Actualizar apariencia de tabs
        for nombre, btn in self.botones_vista.items():
            if nombre == vista:
                # Activo: Color intenso, texto blanco
                # Usamos el color guardado en el botón
                color = getattr(btn, 'color_activo', '#3b82f6')
                btn.config(bg=color, fg="white")
            else:
                # Inactivo: Fondo oscuro, texto gris
                btn.config(bg=THEME_BG, fg=THEME_FG_SEC)
    
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
            self.label_zoom.config(text=f"{porcentaje}%")
    
    def cerrar(self):
        """Cierra la ventana de vistas"""
        if self.window:
            self.window.destroy()
            self.window = None

