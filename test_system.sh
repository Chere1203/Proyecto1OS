#!/bin/bash
# Script de prueba rápida para el sistema de procesamiento multimedia

echo "=== Sistema de Procesamiento Multimedia - Prueba Rápida ==="
echo

# Verificar que estamos en el directorio correcto
if [ ! -f "coordinator.py" ]; then
    echo "Error: Ejecuta este script desde el directorio del proyecto"
    exit 1
fi

# Verificar que ffmpeg esté instalado
if ! command -v ffmpeg &> /dev/null; then
    echo "Advertencia: ffmpeg no está instalado. Las tareas serán simuladas."
    echo "Instala con: brew install ffmpeg"
fi

echo "1. Generando dataset multimedia..."
python generate_test_media.py

echo
echo "2. Iniciando coordinador en background..."
python coordinator.py &
COORDINATOR_PID=$!

# Esperar que el coordinador inicie
sleep 3

echo "3. Iniciando 2 workers en background..."
python worker.py worker-1 &
WORKER1_PID=$!
python worker.py worker-2 &
WORKER2_PID=$!

# Esperar que los workers se conecten
sleep 2

echo "4. Enviando trabajos de prueba..."
python client.py submit "Trabajo de prueba 1"
python client.py submit "Trabajo de prueba 2"

echo
echo "5. Generando carga concurrente (3 clientes, 3 trabajos cada uno)..."
python load_generator.py --clients 3 --jobs 3 --delay 0.5

echo
echo "6. Estado final del sistema:"
python client.py list

echo
echo "7. Dashboard disponible en: http://127.0.0.1:8000/dashboard"
echo
echo "Presiona Ctrl+C para detener todos los procesos..."

# Función de cleanup
cleanup() {
    echo
    echo "Deteniendo procesos..."
    kill $COORDINATOR_PID $WORKER1_PID $WORKER2_PID 2>/dev/null
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT

# Esperar indefinidamente
wait