# ==========================================
# CONFIGURACIÓN Y CONSTANTES
# ==========================================
# ==========================================
# CONFIGURACIÓN Y CONSTANTES GLOBAL
# ==========================================

# Configuración de la Ventana Global (Dashboard)
ANCHO_VENTANA = 1000
ALTO_VENTANA = 700
TITULO_VENTANA = "Simulador de Tráfico - Computación Paralela"

# Configuración del Canvas (Área de Simulación Izquierda)
CANVAS_ANCHO = 700
CANVAS_ALTO = 700 # Cuadrado para el cruce

# Colores (Tema Cyber-Traffic Simulation)
COLOR_FONDO = "#0f172a"        # Azul medianoche profundo (Canvas bg)
COLOR_CALLE = "#1e293b"        # Asfalto azulado oscuro
COLOR_LINEA = "#facc15"        # Amarillo neón para líneas
COLOR_AUTO_ESPERA = "#e74c3c"  # Mantenemos rojo para espera
COLOR_AUTO_CRUZANDO = "#2ecc71" # Verde para movimiento
COLOR_AMBULANCIA = "#ffffff"   # Blanco base para ambulancia (con cruz roja)

# Colores Semáforo Moderno
COLOR_SEMAFORO_CUERPO = "#000000"
COLOR_LUZ_ROJA = "#FF1744"      # Rojo intenso
COLOR_LUZ_AMARILLA = "#FFC107"  # Ámbar
COLOR_LUZ_VERDE = "#00E676"     # Verde brillante
COLOR_LUZ_OFF = "#333333"       # Gris oscuro para luz apagada

# ==========================================
# UI THEME (CYBER-TRAFFIC)
# ==========================================
# Paleta inspirada en imagen de referencia (Azules profundos, Cian, Neón)
THEME_BG = "#0f172a"            # Azul medianoche profundo (Fondo principal)
THEME_BG_SEC = "#1e293b"        # Azul grisáceo oscuro (Paneles, Cards)
THEME_FG = "#f1f5f9"            # Blanco azulado (Texto principal)
THEME_FG_SEC = "#94a3b8"        # Gris azulado (Texto secundario)
THEME_ACCENT = "#38bdf8"        # Cian eléctrico (Acentos, Bordes)
THEME_BORDER = "#334155"        # Borde sutil

# Colores específicos de estado para UI (Vibrantes)
UI_SUCCESS = "#10b981"          # Verde esmeralda neón
UI_DANGER = "#f43f5e"           # Rojo frambuesa neón
UI_WARNING = "#f59e0b"          # Ámbar brillante
UI_INFO = "#3b82f6"             # Azul real brillante

# Coordenadas (Centradas en el Canvas de Simulación)
CENTRO_X, CENTRO_Y = CANVAS_ANCHO // 2, CANVAS_ALTO // 2
ANCHO_CALLE = 100
OFFSET_SEMAFORO = 60 # Distancia del semáforo al centro

# Modos
MODO_PROCESOS = "PROCESOS"
MODO_HILOS = "HILOS"

# >>> CONFIGURACIÓN ACTUAL <<<
MODO_ACTUAL = MODO_PROCESOS

# ==========================================
# CONFIGURACIÓN DE CONCURRENCIA
# ==========================================
# Número de workers (hilos/procesos) que se crearán
# El sistema crea: NUM_SEMAFOROS + NUM_CONTROLADORES workers
NUM_SEMAFOROS = 4  # N, S, E, O
NUM_CONTROLADORES = 1  # Controlador central
NUM_WORKERS_TOTAL = NUM_SEMAFOROS + NUM_CONTROLADORES  # Total: 5 workers

# Probabilidades de llegada de vehículos (por iteración del loop)
# Valores más bajos = menos tráfico
PROBABILIDAD_LLEGADA_NORTE_SUR = 0.2  
PROBABILIDAD_LLEGADA_ESTE_OESTE = 0.1

# ==========================================
# CONFIGURACIÓN DE TIEMPOS DE SEMÁFOROS
# ==========================================
# Tiempos en segundos para cada fase del semáforo
TIEMPO_VERDE = 4.0      # Duración del semáforo en verde (segundos)
TIEMPO_AMARILLO = 1.5   # Duración del semáforo en amarillo (segundos)
# Nota: El tiempo en rojo es automático (mientras los otros están en verde) 

