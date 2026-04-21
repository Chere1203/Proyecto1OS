#!/usr/bin/env python3
"""
Script para generar un dataset multimedia de prueba diverso.
Crea archivos de audio y video con diferentes formatos, duraciones y tamaños.
Requiere ffmpeg instalado en el sistema.
"""

import subprocess
import os
import random

# Configuración del dataset
VIDEO_FORMATS = ['mp4', 'mkv', 'avi', 'mov']
AUDIO_FORMATS = ['mp3', 'wav', 'aac', 'flac']
DURATIONS = [5, 10, 15, 30, 60]  # segundos
RESOLUTIONS = ['640x480', '1280x720', '1920x1080']

def generate_video(filename: str, duration: int, resolution: str, format: str):
    """Genera un video de prueba."""
    if os.path.exists(filename):
        print(f"{filename} ya existe, saltando...")
        return

    # Comando para generar video con patrón de colores y texto
    cmd = [
        'ffmpeg', '-f', 'lavfi',
        '-i', f"testsrc=duration={duration}:size={resolution}:rate=30",
        '-vf', f"drawtext=text='Video {os.path.basename(filename)}':fontsize=30:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '28',
        '-y', filename
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        size = os.path.getsize(filename) / (1024 * 1024)  # MB
        print(f"Video generado: {filename} ({size:.1f} MB)")
    except subprocess.CalledProcessError as e:
        print(f"Error generando {filename}: {e}")

def generate_audio(filename: str, duration: int, format: str):
    """Genera un archivo de audio de prueba."""
    if os.path.exists(filename):
        print(f"{filename} ya existe, saltando...")
        return

    # Comando para generar audio con tono de prueba
    cmd = [
        'ffmpeg', '-f', 'lavfi',
        '-i', f"sine=frequency=440:duration={duration}",
        '-c:a', 'aac' if format in ['mp3', 'aac'] else 'pcm_s16le',
        '-y', filename
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        size = os.path.getsize(filename) / (1024 * 1024)  # MB
        print(f"Audio generado: {filename} ({size:.1f} MB)")
    except subprocess.CalledProcessError as e:
        print(f"Error generando {filename}: {e}")

def create_dataset():
    """Crea un dataset diverso de archivos multimedia."""
    os.makedirs("media", exist_ok=True)

    print("Generando dataset multimedia de prueba...")

    # Generar videos diversos
    video_count = 0
    for duration in DURATIONS:
        for resolution in RESOLUTIONS:
            for fmt in VIDEO_FORMATS:
                if video_count >= 20:  # Limitar a 20 videos
                    break
                filename = f"media/video_{duration}s_{resolution.replace('x', '_')}_{video_count}.{fmt}"
                generate_video(filename, duration, resolution, fmt)
                video_count += 1

    # Generar audios diversos
    audio_count = 0
    for duration in DURATIONS[:3]:  # Solo algunas duraciones para audio
        for fmt in AUDIO_FORMATS:
            if audio_count >= 10:  # Limitar a 10 audios
                break
            filename = f"media/audio_{duration}s_{audio_count}.{fmt}"
            generate_audio(filename, duration, fmt)
            audio_count += 1

    print("Dataset generado exitosamente!")

def list_dataset():
    """Lista los archivos del dataset con metadatos."""
    if not os.path.exists("media"):
        print("Directorio media no existe. Ejecuta primero: python generate_test_media.py")
        return

    print("\n=== DATASET MULTIMEDIA DE PRUEBA ===")
    print("Criterios de construcción:")
    print("- Diversidad de formatos: MP4, MKV, AVI, MOV, MP3, WAV, AAC, FLAC")
    print("- Variedad de duraciones: 5s, 10s, 15s, 30s, 60s")
    print("- Diferentes resoluciones: 480p, 720p, 1080p")
    print("- Tamaños variables para testing de carga")
    print()

    total_files = 0
    total_size = 0

    for filename in sorted(os.listdir("media")):
        filepath = os.path.join("media", filename)
        if os.path.isfile(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            total_files += 1
            total_size += size_mb
            print("30")

    print(f"\nTotal: {total_files} archivos, {total_size:.1f} MB")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_dataset()
    else:
        # Verificar si ffmpeg está disponible
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            create_dataset()
            list_dataset()
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: ffmpeg no está instalado.")
            print("Instala con: brew install ffmpeg (macOS)")
            print("O usa: sudo apt install ffmpeg (Ubuntu/Debian)")
            sys.exit(1)
