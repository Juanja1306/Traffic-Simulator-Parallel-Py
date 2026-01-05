# 🚦 Simulador de Tráfico Paralelo

Simulador de intersección con semáforos que demuestra conceptos de programación concurrente en Python. El sistema permite elegir entre dos modos de ejecución: **procesos** (multiprocessing) o **hilos** (threading), proporcionando una experiencia visual e interactiva para entender las diferencias entre ambos enfoques.

## 📋 Características

- ✅ **Simulación de 4 semáforos** (Norte, Sur, Este, Oeste)
- ✅ **Interfaz gráfica interactiva** con animación de vehículos en tiempo real
- ✅ **Dos modos de ejecución**: Procesos (multiprocessing) o Hilos (threading)
- ✅ **Panel de monitoreo** en tiempo real de workers activos
- ✅ **Estadísticas de tráfico**: tiempo de espera promedio, total de vehículos
- ✅ **Controlador central** que gestiona la sincronización de semáforos
- ✅ **Sistema de eventos** para coordinación entre workers
- ✅ **Soporte multiplataforma** con configuración especial para Windows

## 🎯 Requisitos

- Python 3.7 o superior
- Tkinter (incluido en la mayoría de instalaciones de Python)
- Sistema operativo: Windows, Linux o macOS

## 🚀 Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/tu-usuario/traffic-simulator-parallel.git
cd traffic-simulator-parallel
```

2. No se requieren dependencias adicionales (solo librerías estándar de Python)

## 💻 Uso

Ejecuta el simulador con:

```bash
python main.py
```

Al iniciar, se mostrará una ventana de diálogo para seleccionar el modo de ejecución:

- **PROCESOS**: Usa `multiprocessing` para mayor aislamiento entre workers
- **HILOS**: Usa `threading` para menor overhead y compartición de memoria

### Interfaz Principal

La ventana principal muestra:
- **Intersección visual** con calles y semáforos en las 4 direcciones
- **Semáforos animados** que cambian de color (rojo, amarillo, verde)
- **Vehículos en cola** (rectángulos rojos) esperando en cada dirección
- **Vehículos cruzando** (rectángulos verdes) animados en movimiento
- **Contador de vehículos** por semáforo
- **Estadísticas** en la parte inferior (total de autos, tiempo promedio de espera)

### Panel de Monitoreo

Haz clic en el botón **"📊 Monitoreo"** en la barra superior para abrir el panel de monitoreo que muestra:
- Información del sistema (PID principal, número de workers, estado del GIL)
- Detalles de cada worker (PID/Thread ID, nombre, estado, función)
- Actualización en tiempo real cada segundo

## 📁 Estructura del Proyecto

```
traffic-simulator-parallel/
│
├── main.py                 # Punto de entrada principal
├── config.py               # Configuración y constantes
├── models.py               # Modelos de datos (EstadoSemaforo, Vehiculo, Estadisticas)
├── workers.py              # Lógica de workers (semáforos y controlador)
├── utils.py                # Funciones utilitarias
│
├── gui/
│   ├── __init__.py
│   ├── app.py              # Interfaz gráfica principal
│   └── monitor.py          # Panel de monitoreo de workers
│
└── verificacion/
    ├── verificar_procesos.py
    └── COMANDOS_VERIFICACION.md
```

## ⚙️ Configuración

Puedes modificar los parámetros en `config.py`:

```python
# Número de workers
NUM_SEMAFOROS = 4          # Semáforos (N, S, E, O)
NUM_CONTROLADORES = 1      # Controlador central

# Probabilidades de llegada de vehículos
PROBABILIDAD_LLEGADA_NORTE_SUR = 0.2
PROBABILIDAD_LLEGADA_ESTE_OESTE = 0.1

# Tiempos de semáforos (en segundos)
TIEMPO_VERDE = 4.0
TIEMPO_AMARILLO = 1.5

# Dimensiones de la ventana
ANCHO_VENTANA = 800
ALTO_VENTANA = 600
```

## 🏗️ Arquitectura

### Componentes Principales

1. **Workers de Semáforos** (4 workers)
   - Cada semáforo (N, S, E, O) corre en su propio proceso/hilo
   - Gestiona su cola de vehículos
   - Responde a eventos de inicio/fin del controlador
   - Actualiza la GUI con su estado actual

2. **Controlador Central** (1 worker)
   - Coordina la sincronización de semáforos
   - Activa semáforos en pares (N-S simultáneamente, luego E-O)
   - Gestiona ciclos de tráfico

3. **Interfaz Gráfica** (Main Thread)
   - Procesa mensajes de la cola de comunicación
   - Actualiza la visualización en tiempo real
   - Muestra estadísticas y animaciones

### Comunicación

- **Cola de mensajes**: Comunicación entre workers y GUI
- **Eventos**: Sincronización entre controlador y semáforos
  - `eventos_inicio`: Señal para activar semáforo (verde)
  - `eventos_fin`: Confirmación de que el semáforo terminó su ciclo

### Modos de Ejecución

#### Modo Procesos (multiprocessing)
- Mayor aislamiento entre workers
- Memoria independiente por proceso
- Mejor para CPU-bound tasks
- En Windows usa `spawn` method

#### Modo Hilos (threading)
- Menor overhead
- Comparten memoria y espacio de proceso
- Afectados por el GIL (Global Interpreter Lock)
- Mejor para I/O-bound tasks

## 🛠️ Tecnologías Utilizadas

- **Python 3.7+**: Lenguaje de programación
- **Tkinter**: Interfaz gráfica de usuario
- **multiprocessing**: Para ejecución con procesos
- **threading**: Para ejecución con hilos
- **collections.deque**: Estructura de datos para colas de vehículos
- **enum**: Para estados de semáforos

## 📊 Funcionalidades Detalladas

### Simulación de Tráfico
- Llegada aleatoria de vehículos según probabilidades configuradas
- Colas de espera por dirección
- Cruce de vehículos cuando el semáforo está en verde
- Cálculo de tiempo de espera por vehículo

### Visualización
- Semáforos con colores realistas (rojo, amarillo, verde)
- Animación fluida de vehículos cruzando la intersección
- Representación visual de colas de espera
- Contadores en tiempo real

### Monitoreo
- Información detallada de cada worker
- Estado del sistema (PID, Thread ID, estado de vida)
- Información del GIL (Global Interpreter Lock)
- Actualización automática cada segundo

## 🎓 Propósito Educativo

Este proyecto es ideal para:
- Entender diferencias entre procesos e hilos en Python
- Aprender programación concurrente y paralela
- Visualizar sincronización con eventos
- Comprender comunicación entre procesos/hilos
- Estudiar el impacto del GIL en threading

## 📝 Notas

- En Windows, el sistema usa `spawn` method para multiprocessing (configurado automáticamente)
- El GIL afecta el rendimiento en modo threading para tareas CPU-intensivas
- Los workers son daemon, por lo que terminan cuando el proceso principal termina
- El controlador ejecuta un número limitado de ciclos (configurable en `workers.py`)

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto y está disponible para uso educativo y de aprendizaje.

## 👤 Autor

Desarrollado como proyecto educativo para demostrar conceptos de programación paralela y concurrente.

---

**¡Disfruta simulando el tráfico! 🚗🚦**

