import argparse
import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"

async def submit_job(name: str):
    payload = {
        "name": name,
        "tasks": [
            {"type": "convert", "source": "media/source_video.mp4", "target": "media/output_video.mkv"},
            {"type": "extract_audio", "source": "media/source_video.mp4", "target": "media/source_audio.mp3"},
            {"type": "thumbnail", "source": "media/source_video.mp4", "target": "media/cover.png"},
        ],
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/jobs", json=payload)
        response.raise_for_status()
        print("Trabajo enviado:", response.json())


async def list_jobs():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/jobs")
        response.raise_for_status()
        jobs = response.json()
        for job in jobs:
            print(f"{job['id']} - {job['name']} - {job['status']} - {job['progress']:.0f}%")


async def get_job(job_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/jobs/{job_id}")
        response.raise_for_status()
        job = response.json()
        print(job)


def main():
    parser = argparse.ArgumentParser(description="Cliente de pruebas para la plataforma multimedia")
    subparsers = parser.add_subparsers(dest="command")

    parser_submit = subparsers.add_parser("submit", help="Enviar un trabajo de prueba")
    parser_submit.add_argument("name", nargs="?", default="Trabajo multimedia de prueba")

    parser_list = subparsers.add_parser("list", help="Listar trabajos")

    parser_status = subparsers.add_parser("status", help="Consultar el estado de un trabajo")
    parser_status.add_argument("job_id")

    args = parser.parse_args()
    if args.command == "submit":
        asyncio.run(submit_job(args.name))
    elif args.command == "list":
        asyncio.run(list_jobs())
    elif args.command == "status":
        asyncio.run(get_job(args.job_id))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
