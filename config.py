# ==========================================
# CONFIGURACIÓN Y CONSTANTES
# ==========================================
ANCHO_VENTANA = 800
ALTO_VENTANA = 600
COLOR_FONDO = "#212121"  # Fondo más oscuro, estilo dark mode moderno
COLOR_CALLE = "#424242"  # Calles gris oscuro mate
COLOR_LINEA = "#FFEB3B"  # Amarillo vibrante para líneas
COLOR_AUTO_ESPERA = "#FF5252"  # Rojo coral vibrante
COLOR_AUTO_CRUZANDO = "#69F0AE" # Verde menta neón
COLOR_AMBULANCIA = "#FF9800"    # Naranja intenso

# Colores Semáforo Moderno
COLOR_SEMAFORO_CUERPO = "#000000"
COLOR_LUZ_ROJA = "#FF1744"      # Rojo intenso
COLOR_LUZ_AMARILLA = "#FFC107"  # Ámbar
COLOR_LUZ_VERDE = "#00E676"     # Verde brillante
COLOR_LUZ_OFF = "#333333"       # Gris oscuro para luz apagada

# Coordenadas
CENTRO_X, CENTRO_Y = ANCHO_VENTANA // 2, ALTO_VENTANA // 2
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

