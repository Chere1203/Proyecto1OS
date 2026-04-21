#!/usr/bin/env python3
"""
Generador de carga concurrente para el sistema de procesamiento multimedia.
Simula múltiples clientes enviando trabajos simultáneamente.
"""

import asyncio
import httpx
import random
import argparse
import time
from typing import List, Dict
import os

BASE_URL = "http://127.0.0.1:8000"

# Configuración de carga
TASK_TYPES = ["convert", "extract_audio", "thumbnail", "metadata", "lyrics", "organize"]
VIDEO_FILES = []
AUDIO_FILES = []

def load_media_files():
    """Carga la lista de archivos multimedia disponibles."""
    global VIDEO_FILES, AUDIO_FILES
    if not os.path.exists("media"):
        print("Directorio media no existe. Genera el dataset primero.")
        return False

    for filename in os.listdir("media"):
        filepath = os.path.join("media", filename)
        if os.path.isfile(filepath):
            if filename.endswith(('.mp4', '.mkv', '.avi', '.mov')):
                VIDEO_FILES.append(filepath)
            elif filename.endswith(('.mp3', '.wav', '.aac', '.flac')):
                AUDIO_FILES.append(filepath)
    return len(VIDEO_FILES) > 0 or len(AUDIO_FILES) > 0

def generate_random_job(job_id: int) -> Dict:
    """Genera un trabajo aleatorio basado en archivos disponibles."""
    tasks = []

    # Seleccionar archivos aleatorios para las tareas
    if VIDEO_FILES:
        video_file = random.choice(VIDEO_FILES)
        # Conversión de formato
        if random.random() < 0.3:
            tasks.append({
                "type": "convert",
                "source": video_file,
                "target": video_file.replace('.mp4', '_converted.mkv').replace('.mkv', '_converted.mp4')
            })

        # Extracción de audio
        if random.random() < 0.4:
            tasks.append({
                "type": "extract_audio",
                "source": video_file,
                "target": video_file.replace('.mp4', '.mp3').replace('.mkv', '.mp3')
            })

        # Generación de thumbnail
        if random.random() < 0.5:
            tasks.append({
                "type": "thumbnail",
                "source": video_file,
                "target": video_file.replace('.mp4', '_thumb.png').replace('.mkv', '_thumb.png')
            })

    # Tareas de metadata y organización (siempre incluir algunas)
    if random.random() < 0.6:
        source = random.choice(VIDEO_FILES + AUDIO_FILES) if VIDEO_FILES or AUDIO_FILES else "media/sample.mp4"
        tasks.append({
            "type": random.choice(["metadata", "lyrics", "organize"]),
            "source": source,
            "target": source + "_processed"
        })

    return {
        "name": f"Trabajo de carga #{job_id}",
        "tasks": tasks
    }

async def send_job(client: httpx.AsyncClient, job_data: Dict) -> Dict:
    """Envía un trabajo al coordinador."""
    try:
        response = await client.post(f"{BASE_URL}/jobs", json=job_data, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error enviando trabajo: {e}")
        return None

async def monitor_system(client: httpx.AsyncClient, duration: int):
    """Monitorea el estado del sistema durante la carga."""
    start_time = time.time()
    jobs_sent = 0
    jobs_completed = 0

    while time.time() - start_time < duration:
        try:
            # Obtener estado actual
            response = await client.get(f"{BASE_URL}/jobs", timeout=5.0)
            if response.status_code == 200:
                jobs = response.json()
                completed = sum(1 for job in jobs if job['status'] == 'completed')
                running = sum(1 for job in jobs if job['status'] == 'running')
                pending = sum(1 for job in jobs if job['status'] == 'pending')

                print(f"[{int(time.time() - start_time)}s] Jobs: {len(jobs)} total, {pending} pendientes, {running} ejecutándose, {completed} completados")

            await asyncio.sleep(2)
        except Exception as e:
            print(f"Error monitoreando: {e}")
            await asyncio.sleep(2)

async def load_generator(num_clients: int, jobs_per_client: int, delay_between_jobs: float):
    """Genera carga con múltiples clientes concurrentes."""
    if not load_media_files():
        print("No hay archivos multimedia disponibles.")
        return

    print(f"Iniciando carga con {num_clients} clientes, {jobs_per_client} trabajos cada uno")
    print(f"Archivos disponibles: {len(VIDEO_FILES)} videos, {len(AUDIO_FILES)} audios")

    async with httpx.AsyncClient() as client:
        # Iniciar monitoreo en background
        monitor_task = asyncio.create_task(monitor_system(client, (num_clients * jobs_per_client * delay_between_jobs) + 30))

        # Crear tareas para clientes
        client_tasks = []
        for client_id in range(num_clients):
            task = asyncio.create_task(
                client_worker(client, client_id, jobs_per_client, delay_between_jobs)
            )
            client_tasks.append(task)

        # Esperar que todos los clientes terminen
        results = await asyncio.gather(*client_tasks, return_exceptions=True)

        # Mostrar resultados
        total_jobs = sum(r for r in results if isinstance(r, int))
        print(f"\nCarga completada: {total_jobs} trabajos enviados por {num_clients} clientes")

        # Esperar un poco más para que termine el monitoreo
        await asyncio.sleep(5)

async def client_worker(client: httpx.AsyncClient, client_id: int, num_jobs: int, delay: float) -> int:
    """Trabajador que simula un cliente enviando trabajos."""
    jobs_sent = 0

    for i in range(num_jobs):
        job_data = generate_random_job(client_id * num_jobs + i)
        if job_data["tasks"]:  # Solo enviar si hay tareas
            result = await send_job(client, job_data)
            if result:
                jobs_sent += 1
                print(f"Cliente {client_id}: Trabajo {i+1}/{num_jobs} enviado (ID: {result.get('id', 'N/A')})")

        # Delay aleatorio entre trabajos
        await asyncio.sleep(delay + random.uniform(0, delay))

    return jobs_sent

def main():
    parser = argparse.ArgumentParser(description="Generador de carga concurrente para el sistema multimedia")
    parser.add_argument("--clients", "-c", type=int, default=3, help="Número de clientes concurrentes")
    parser.add_argument("--jobs", "-j", type=int, default=5, help="Trabajos por cliente")
    parser.add_argument("--delay", "-d", type=float, default=2.0, help="Delay base entre trabajos (segundos)")

    args = parser.parse_args()

    print("Generador de Carga - Sistema de Procesamiento Multimedia")
    print("=" * 50)
    print(f"Clientes: {args.clients}")
    print(f"Trabajos por cliente: {args.jobs}")
    print(f"Delay entre trabajos: {args.delay}s")
    print()

    try:
        asyncio.run(load_generator(args.clients, args.jobs, args.delay))
    except KeyboardInterrupt:
        print("\nCarga interrumpida por usuario")
    except Exception as e:
        print(f"Error en generador de carga: {e}")

if __name__ == "__main__":
    main()