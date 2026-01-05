# ==========================================
# CONFIGURACIÓN Y CONSTANTES
# ==========================================
ANCHO_VENTANA = 800
ALTO_VENTANA = 600
COLOR_FONDO = "#2c3e50"
COLOR_CALLE = "#34495e"
COLOR_LINEA = "#f1c40f"
COLOR_AUTO_ESPERA = "#e74c3c"  # Rojo para autos esperando
COLOR_AUTO_CRUZANDO = "#2ecc71" # Verde para autos moviéndose
COLOR_AMBULANCIA = "#f39c12"    # Naranja para ambulancia

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

