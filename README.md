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
- ✅ **Sistema de ambulancias** con prioridad absoluta y efectos visuales
- ✅ **Panel de vistas de imágenes** con diferentes perspectivas de la intersección
- ✅ **Zoom interactivo** en las vistas de imágenes (con soporte de rueda del mouse)
- ✅ **Soporte multiplataforma** con configuración especial para Windows

## 🎯 Requisitos

- Python 3.7 o superior
- Tkinter (incluido en la mayoría de instalaciones de Python)
- Sistema operativo: Windows, Linux o macOS
- **Opcional**: Pillow (PIL) para mejor soporte de imágenes y funcionalidad de zoom
  ```bash
  pip install Pillow
  ```

## 🚀 Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/tu-usuario/traffic-simulator-parallel.git
cd traffic-simulator-parallel
```

2. **(Opcional)** Instala Pillow para mejor soporte de imágenes y zoom en el panel de vistas:
```bash
pip install Pillow
```

**Nota**: El simulador funciona sin Pillow, pero algunas funcionalidades del panel de vistas estarán limitadas.

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
- **Vehículos en cola** (rectángulos rojos) esperando en cada dirección (hasta 12 visibles por dirección)
- **Vehículos cruzando** (rectángulos verdes) animados en movimiento
- **Contador de vehículos** por semáforo
- **Estadísticas** en la parte inferior (total de autos, tiempo promedio de espera)
- **Barra de herramientas** con botones para:
  - 📊 **Monitoreo**: Abre el panel de monitoreo de workers
  - 🖼️ **Vistas**: Abre el panel de vistas de imágenes
  - 🚑 **Ambulancia**: Activa una ambulancia de emergencia con prioridad
  - ⬅️ **Volver atrás**: Regresa a la selección de modo

### Panel de Monitoreo

Haz clic en el botón **"📊 Monitoreo"** en la barra superior para abrir el panel de monitoreo que muestra:
- Información del sistema (PID principal, número de workers, estado del GIL)
- Detalles de cada worker (PID/Thread ID, nombre, estado, función)
- Layout en grid 3x2 mostrando el proceso principal y los 5 workers
- Actualización en tiempo real cada segundo

### Panel de Vistas de Imágenes

Haz clic en el botón **"🖼️ Vistas"** para abrir el panel de vistas que permite:
- Visualizar la intersección desde diferentes perspectivas:
  - **Norte**: Vista desde el norte
  - **Sur**: Vista desde el sur
  - **Este**: Vista desde el este
  - **Oeste**: Vista desde el oeste
  - **Aérea**: Vista aérea de la intersección
- **Zoom interactivo**: Usa los botones o la rueda del mouse para hacer zoom (10% - 500%)
- **Scroll**: Navega por imágenes grandes con barras de desplazamiento
- **Requisito**: Las imágenes deben estar en la carpeta `Images/` del proyecto

### Sistema de Ambulancias

El botón **"🚑 Ambulancia"** permite activar una ambulancia de emergencia:
- **Prioridad absoluta**: La ambulancia interrumpe el ciclo normal de semáforos
- **Dirección aleatoria**: Se selecciona automáticamente una dirección (N, S, E, O)
- **Efecto visual**: 
  - La ambulancia aparece en color naranja con etiqueta "AMB"
  - Efecto de sirena con parpadeo del fondo del canvas
  - Todos los semáforos se ponen en rojo excepto el de la dirección de la ambulancia
- **Duración**: La ambulancia cruza en aproximadamente 2 segundos
- El botón se deshabilita mientras hay una ambulancia activa

## 📁 Estructura del Proyecto

```
traffic-simulator-parallel/
│
├── main.py                 # Punto de entrada principal
├── config.py               # Configuración y constantes
├── models.py               # Modelos de datos (EstadoSemaforo, Vehiculo, Ambulancia, Estadisticas)
├── workers.py              # Lógica de workers (semáforos y controlador)
├── utils.py                # Funciones utilitarias
│
├── gui/
│   ├── __init__.py
│   ├── app.py              # Interfaz gráfica principal (incluye panel de vistas)
│   └── monitor.py          # Panel de monitoreo de workers
│
├── Images/                 # Imágenes de vistas de la intersección
│   ├── Norte.png
│   ├── Sur.png
│   ├── Este.png
│   ├── Oeste.png
│   └── aerea.png
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

# Colores
COLOR_AUTO_ESPERA = "#e74c3c"      # Rojo para autos esperando
COLOR_AUTO_CRUZANDO = "#2ecc71"   # Verde para autos moviéndose
COLOR_AMBULANCIA = "#f39c12"      # Naranja para ambulancia
```

## 🏗️ Arquitectura

### Componentes Principales

1. **Workers de Semáforos** (4 workers)
   - Cada semáforo (N, S, E, O) corre en su propio proceso/hilo
   - Gestiona su cola de vehículos usando `deque`
   - Responde a eventos de inicio/fin del controlador
   - Detecta y responde a emergencias de ambulancias
   - Actualiza la GUI con su estado actual
   - Simula llegada aleatoria de vehículos según probabilidades configuradas

2. **Controlador Central** (1 worker)
   - Coordina la sincronización de semáforos
   - Activa semáforos en pares (N-S simultáneamente, luego E-O)
   - Gestiona ciclos de tráfico (10 ciclos por defecto)
   - Pausa el ciclo normal cuando hay una ambulancia activa
   - Espera confirmación de finalización de cada fase

3. **Interfaz Gráfica** (Main Thread)
   - Procesa mensajes de la cola de comunicación
   - Actualiza la visualización en tiempo real
   - Muestra estadísticas y animaciones
   - Gestiona el sistema de ambulancias y efectos visuales
   - Proporciona paneles de monitoreo y vistas de imágenes

### Comunicación

- **Cola de mensajes**: Comunicación entre workers y GUI
  - Mensajes: `UPDATE`, `ANIMACION_CRUCE`, `STATS`, `CICLO`, `FIN`, `AMBULANCIA_CRUZANDO`, `AMBULANCIA_COMPLETADA`
- **Eventos**: Sincronización entre controlador y semáforos
  - `eventos_inicio`: Señal para activar semáforo (verde)
  - `eventos_fin`: Confirmación de que el semáforo terminó su ciclo
  - `evento_ambulancia`: Señal de activación de ambulancia
  - `evento_ambulancia_activa`: Indica si hay una ambulancia activa
  - `direccion_ambulancia`: Dirección desde la que viene la ambulancia (compartida entre workers)

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
- **Pillow (PIL)** (opcional): Para mejor manejo de imágenes y funcionalidad de zoom

## 📊 Funcionalidades Detalladas

### Simulación de Tráfico
- Llegada aleatoria de vehículos según probabilidades configuradas
- Colas de espera por dirección (usando `deque` para eficiencia)
- Cruce de vehículos cuando el semáforo está en verde
- Cálculo de tiempo de espera por vehículo
- Sistema de prioridad para ambulancias que interrumpe el ciclo normal

### Visualización
- Semáforos con colores realistas (rojo, amarillo, verde)
- Animación fluida de vehículos cruzando la intersección
- Representación visual de colas de espera (hasta 12 vehículos visibles por dirección)
- Contadores en tiempo real por semáforo
- Animación de ambulancias con color distintivo (naranja) y etiqueta "AMB"
- Efecto visual de sirena con parpadeo del fondo durante emergencias
- Líneas de parada (stop lines) en cada dirección

### Monitoreo
- Información detallada de cada worker
- Estado del sistema (PID, Thread ID, estado de vida)
- Información del GIL (Global Interpreter Lock)
- Layout en grid 3x2 mostrando proceso principal y workers
- Actualización automática cada segundo
- Diferenciación visual entre procesos e hilos

### Vistas de Imágenes
- Visualización de la intersección desde 5 perspectivas diferentes
- Zoom interactivo con rueda del mouse o botones (10% - 500%)
- Scroll para navegar imágenes grandes
- Soporte mejorado con Pillow (redimensionamiento de alta calidad)

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
- El controlador ejecuta un número limitado de ciclos (10 por defecto, configurable en `workers.py`)
- Las ambulancias tienen prioridad absoluta e interrumpen cualquier ciclo de semáforo
- El botón "Volver atrás" permite cambiar de modo sin cerrar completamente la aplicación
- Las imágenes en `Images/` son opcionales; si no existen, el panel de vistas mostrará un error
- Se recomienda instalar Pillow para mejor experiencia con el panel de vistas (zoom y redimensionamiento)

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

