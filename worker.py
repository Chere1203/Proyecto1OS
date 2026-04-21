import asyncio
import httpx
import argparse
import random
from datetime import datetime
import ffmpeg
import os
import subprocess
import psutil

BASE_URL = "http://127.0.0.1:8000"

# Verificar si ffmpeg está disponible
FFMPEG_AVAILABLE = False
try:
    subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    FFMPEG_AVAILABLE = True
except (subprocess.CalledProcessError, FileNotFoundError):
    print("Advertencia: ffmpeg no está instalado. Las tareas multimedia serán simuladas.")
    FFMPEG_AVAILABLE = False

def get_system_metrics():
    """Obtiene métricas del sistema."""
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        "cpu_percent": cpu,
        "memory_percent": memory.percent,
        "memory_used_mb": memory.used / 1024 / 1024,
        "disk_usage_percent": disk.percent,
        "timestamp": datetime.utcnow().isoformat()
    }

async def process_task(task: dict) -> str:
    task_type = task["type"]
    source = task["source"]
    target = task["target"]

    try:
        if not FFMPEG_AVAILABLE and task_type in ["convert", "extract_audio", "thumbnail"]:
            # Simular si ffmpeg no está disponible
            await asyncio.sleep(random.uniform(2.0, 5.0))
            return f"Simulación: {task_type} completado para {source} -> {target}"

        if task_type == "convert":
            # Convertir formato de video (ej: mp4 a mkv)
            ffmpeg.input(source).output(target).run(overwrite_output=True)
            return f"Conversión completada: {source} -> {target}"
        elif task_type == "extract_audio":
            # Extraer audio
            ffmpeg.input(source).output(target, vn=None, acodec='mp3').run(overwrite_output=True)
            return f"Audio extraído: {source} -> {target}"
        elif task_type == "thumbnail":
            # Generar thumbnail
            ffmpeg.input(source).filter('thumbnail').output(target, vframes=1).run(overwrite_output=True)
            return f"Thumbnail generado: {source} -> {target}"
        elif task_type == "metadata":
            # Simular consulta de metadatos
            await asyncio.sleep(1.0)
            return f"Metadatos de {source}: duración=10s, codec=h264"
        elif task_type == "lyrics":
            # Simular integración de letras
            await asyncio.sleep(1.0)
            return f"Letras integradas para {source}"
        elif task_type == "organize":
            # Simular organización de archivos
            await asyncio.sleep(1.0)
            return f"Archivos organizados desde {source}"
        else:
            raise ValueError(f"Tipo de tarea desconocido: {task_type}")
    except ffmpeg.Error as e:
        raise Exception(f"Error en ffmpeg: {e.stderr.decode()}")
    except Exception as e:
        raise Exception(f"Error procesando tarea: {str(e)}")



async def poll_loop(worker_id: str):
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                # Enviar métricas con cada poll
                metrics = get_system_metrics()
                poll_data = {"worker_id": worker_id, "metrics": metrics}

                response = await client.post(f"{BASE_URL}/workers/poll", json=poll_data)
                if response.status_code == 204:
                    print("No hay tareas pendientes. Esperando...")
                    await asyncio.sleep(2.0)
                    continue
                response.raise_for_status()
                task = response.json()
                print(f"Worker {worker_id} recibió tarea {task['id']} ({task['type']})")
                output = await process_task(task)
                update = {
                    "job_id": task["job_id"],
                    "task_id": task["id"],
                    "worker_id": worker_id,
                    "status": "completed",
                    "output": output,
                }
                await client.post(f"{BASE_URL}/workers/status", json=update)
                print(f"Worker {worker_id} completó tarea {task['id']}")
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 204:
                    await asyncio.sleep(2.0)
                    continue
                print(f"Error HTTP en worker: {exc}")
                await asyncio.sleep(3.0)
            except Exception as exc:
                print(f"Error procesando tarea: {exc}")
                # Reportar error al coordinador
                try:
                    update = {
                        "job_id": task["job_id"],
                        "task_id": task["id"],
                        "worker_id": worker_id,
                        "status": "failed",
                        "output": str(exc),
                    }
                    await client.post(f"{BASE_URL}/workers/status", json=update)
                except:
                    pass
                await asyncio.sleep(3.0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Worker para procesar tareas multimedia")
    parser.add_argument("worker_id", nargs="?", default=f"worker-{random.randint(1000,9999)}")
    args = parser.parse_args()
    print(f"Iniciando worker {args.worker_id}")
    asyncio.run(poll_loop(args.worker_id))
