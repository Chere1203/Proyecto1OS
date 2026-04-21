import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List, Optional

from common import Job, JobStatus, JobTask, WorkerStatus, WorkerMetrics, new_job_id, new_task_id, TaskType

app = FastAPI(title="Coordinador de Procesamiento Multimedia")

jobs: Dict[str, Job] = {}
queue: List[str] = []
workers: Dict[str, WorkerStatus] = {}


class JobCreate(BaseModel):
    name: str
    tasks: List[Dict[str, str]]


class WorkerPoll(BaseModel):
    worker_id: str
    metrics: Optional[Dict] = None


class TaskUpdate(BaseModel):
    job_id: str
    task_id: str
    worker_id: str
    status: JobStatus
    output: Optional[str] = None


@app.post("/jobs", response_model=Job)
async def submit_job(payload: JobCreate):
    job_id = new_job_id()
    tasks = []
    for entry in payload.tasks:
        task = JobTask(
            id=new_task_id(),
            type=TaskType(entry["type"]),
            source=entry["source"],
            target=entry["target"],
        )
        tasks.append(task)

    job = Job(id=job_id, name=payload.name, tasks=tasks, status=JobStatus.pending)
    jobs[job_id] = job
    queue.append(job_id)
    return job


@app.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return jobs[job_id]


@app.get("/jobs")
async def list_jobs():
    return list(jobs.values())


@app.post("/workers/poll")
async def poll_task(payload: WorkerPoll):
    if payload.worker_id not in workers:
        workers[payload.worker_id] = WorkerStatus(worker_id=payload.worker_id, last_seen=datetime.utcnow().isoformat())
    workers[payload.worker_id].last_seen = datetime.utcnow().isoformat()

    # Actualizar métricas si se enviaron
    if payload.metrics:
        workers[payload.worker_id].metrics = WorkerMetrics(**payload.metrics)

    for job_id in queue:
        job = jobs[job_id]
        for task in job.tasks:
            if task.status == JobStatus.pending:
                task.status = JobStatus.running
                task.worker = payload.worker_id
                workers[payload.worker_id].active_task = task.id
                job.status = JobStatus.running
                update_progress(job)
                task_data = task.dict()
                task_data["job_id"] = job_id
                return task_data

    raise HTTPException(status_code=204, detail="No hay tareas pendientes")


@app.post("/workers/status")
async def update_task(payload: TaskUpdate):
    if payload.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    job = jobs[payload.job_id]
    task = next((t for t in job.tasks if t.id == payload.task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    task.status = payload.status
    task.output = payload.output
    if payload.status == JobStatus.completed:
        task.worker = payload.worker_id
    if payload.worker_id in workers:
        workers[payload.worker_id].active_task = None

    if all(t.status == JobStatus.completed for t in job.tasks):
        job.status = JobStatus.completed
        queue.remove(job.id)
    elif any(t.status == JobStatus.running for t in job.tasks):
        job.status = JobStatus.running
    elif any(t.status == JobStatus.failed for t in job.tasks):
        job.status = JobStatus.failed
    else:
        job.status = JobStatus.pending
    update_progress(job)
    return {"status": "ok"}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    job_rows = []
    for job in jobs.values():
        job_rows.append(f"<tr><td>{job.id}</td><td>{job.name}</td><td>{job.status}</td><td>{job.progress:.0f}%</td><td>{len(job.tasks)}</td></tr>")
    worker_rows = []
    total_cpu = 0
    total_memory = 0
    active_workers = 0
    for worker in workers.values():
        metrics_info = "Sin datos"
        if worker.metrics:
            metrics_info = f"CPU: {worker.metrics.cpu_percent:.1f}% | Mem: {worker.metrics.memory_percent:.1f}% ({worker.metrics.memory_used_mb:.0f}MB)"
            total_cpu += worker.metrics.cpu_percent
            total_memory += worker.metrics.memory_percent
            active_workers += 1
        worker_rows.append(f"<tr><td>{worker.worker_id}</td><td>{worker.active_task or 'ninguna'}</td><td>{worker.last_seen}</td><td>{metrics_info}</td></tr>")

    # Métricas del sistema
    system_metrics = ""
    if active_workers > 0:
        avg_cpu = total_cpu / active_workers
        avg_memory = total_memory / active_workers
        system_metrics = f"""
        <h2>Métricas del Sistema</h2>
        <p>Workers activos: {active_workers}</p>
        <p>CPU promedio: {avg_cpu:.1f}%</p>
        <p>Memoria promedio: {avg_memory:.1f}%</p>
        <p>Trabajos en cola: {len(queue)}</p>
        <p>Tareas pendientes: {sum(len(job.tasks) for job in jobs.values() if job.status in ['pending', 'running'])}</p>
        """

    html = f"""
    <html><head><title>Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .metrics {{ background-color: #e8f4fd; padding: 10px; border-radius: 5px; }}
    </style>
    </head><body>
    <h1>Dashboard de Coordinador</h1>
    <h2>Trabajos</h2>
    <table border='1'><tr><th>ID</th><th>Nombre</th><th>Estado</th><th>Progreso</th><th>Tareas</th></tr>{''.join(job_rows)}</table>
    <h2>Workers</h2>
    <table border='1'><tr><th>ID</th><th>Tarea activa</th><th>Último visto</th><th>Métricas</th></tr>{''.join(worker_rows)}</table>
    {system_metrics}
    <p>Use la API REST para enviar trabajos y monitorear el sistema.</p>
    </body></html>
    """
    return html


def update_progress(job: Job):
    total = len(job.tasks)
    completed = sum(1 for task in job.tasks if task.status == JobStatus.completed)
    job.progress = 100.0 * completed / total if total else 0.0


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
