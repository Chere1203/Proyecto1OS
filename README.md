# Proyecto 1 - Plataforma Distribuida de Procesamiento Multimedia

Este proyecto es una base en Python para implementar una plataforma distribuida de procesamiento multimedia con los siguientes componentes:

- `coordinator.py`: nodo planificador + dashboard
- `worker.py`: nodo worker que consume tareas desde el coordinador
- `client.py`: cliente de pruebas para enviar trabajos y consultar estado
- `common.py`: modelos compartidos entre componentes
- `generate_test_media.py`: script para generar dataset multimedia de prueba
- `load_generator.py`: generador de carga concurrente para testing
- `generate_test_media.py`: script para generar archivos multimedia de prueba

## Requisitos

- Python 3.10+ (se está usando Python 3.14 en este espacio de trabajo)
- `fastapi`, `uvicorn`, `httpx`, `pydantic`, `ffmpeg-python`, `psutil`
- **ffmpeg** instalado en el sistema (para procesamiento multimedia real)

Instala dependencias Python con:

```bash
python -m pip install -r requirements.txt
```

### Instalación de ffmpeg (macOS)

```bash
# Instalar Homebrew si no lo tienes
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar ffmpeg
brew install ffmpeg
```

### Generar archivos de prueba

```bash
python generate_test_media.py --extende
```

Esto crea un video de prueba en `media/source_video.mp4`.

## Cómo ejecutar

1. Inicia el coordinador:

```bash
python coordinator.py
```

2. Inicia uno o más workers en terminales independientes:

```bash
python worker.py worker-1
python worker.py worker-2
```

3. Envía un trabajo de prueba desde el cliente:

```bash
python client.py submit "Mi trabajo multimedia"
```

4. Consulta el estado de los trabajos:

```bash
python client.py list
```

5. Abre el dashboard en el navegador:

```
http://127.0.0.1:8000/dashboard
```

## Tipos de tareas implementadas

- `convert`: Convierte formato de video (ej: mp4 a mkv)
- `extract_audio`: Extrae audio de video a mp3
- `thumbnail`: Genera imagen de portada del video
- `metadata`: Consulta metadatos (simulado)
- `lyrics`: Integración de letras (simulado)
- `organize`: Organización de archivos (simulado)

## Arquitectura propuesta

- El coordinador recibe trabajos y mantiene una cola de tareas.
- Los workers consultan al coordinador para obtener tareas pendientes.
- Cada worker procesa una tarea usando ffmpeg y reporta el estado de vuelta al coordinador.
- El dashboard muestra trabajos activos, completados y workers registrados.
- **Monitoreo de recursos**: Los workers reportan métricas de CPU, memoria y disco al coordinador.

## Características de monitoreo

- **Métricas por worker**: CPU, memoria usada, uso de disco
- **Métricas del sistema**: Promedios de CPU/memoria, trabajos en cola, tareas pendientes
- **Dashboard en tiempo real**: Actualización automática cada 5 segundos
- **Estado de workers**: Activos, tareas asignadas, último reporte

## Dataset Multimedia de Prueba

El proyecto incluye un dataset diverso de archivos multimedia generado automáticamente:

### Generación del Dataset

```bash
python generate_test_media.py
```

Esto crea:
- **20 videos** en formatos MP4, MKV, AVI, MOV
- **10 archivos de audio** en formatos MP3, WAV, AAC, FLAC
- Variedad de duraciones: 5s, 10s, 15s, 30s, 60s
- Diferentes resoluciones: 480p, 720p, 1080p

### Listar el Dataset

```bash
python generate_test_media.py list
```

### Criterios del Dataset

- **Diversidad de formatos**: Cubre los principales formatos multimedia
- **Variedad de tamaños**: Archivos de diferentes duraciones y resoluciones
- **Realismo**: Archivos generados con contenido visual y auditivo
- **Escalabilidad**: Fácil de expandir para testing de carga

## Generación de Carga Concurrente

Para simular escenarios de carga alta, incluye un generador de carga concurrente:

### Uso Básico

```bash
python load_generator.py
```

### Opciones Avanzadas

```bash
# 5 clientes, 10 trabajos cada uno, 3s entre trabajos
python load_generator.py --clients 5 --jobs 10 --delay 3.0
```

### Características

- **Múltiples clientes concurrentes**: Simula varios usuarios enviando trabajos
- **Trabajos aleatorios**: Genera tareas basadas en archivos disponibles
- **Monitoreo en tiempo real**: Muestra progreso del sistema durante la carga
- **Configurable**: Número de clientes, trabajos y delays personalizables

## Prueba Rápida del Sistema

Para probar todo el sistema de una vez:

```bash
./test_system.sh
```

Este script:
1. Genera el dataset multimedia
2. Inicia coordinador y workers
3. Envía trabajos de prueba
4. Genera carga concurrente
5. Muestra el estado final

Presiona Ctrl+C para detener todos los procesos.

## Ejemplo Completo de Uso

```bash
# 1. Generar dataset multimedia
python generate_test_media.py

# 2. Iniciar coordinador
python coordinator.py

# 3. Iniciar workers (en terminales separadas)
python worker.py worker-1
python worker.py worker-2

# 4. Generar carga concurrente
python load_generator.py --clients 3 --jobs 5 --delay 1.0

# 5. Monitorear en el navegador
open http://127.0.0.1:8000/dashboard

# 6. Ver estado de trabajos
python client.py list
```

## Próximos pasos

- Agregar prioridades y reintentos en la cola de tareas.
- Añadir persistencia de trabajos en disco o base de datos.
- Incluir métricas de CPU/memoria en el dashboard.
- Implementar procesamiento real para metadata, lyrics y organize.
