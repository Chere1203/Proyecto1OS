from enum import Enum
from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class TaskType(str, Enum):
    convert = "convert"
    extract_audio = "extract_audio"
    thumbnail = "thumbnail"
    metadata = "metadata"
    lyrics = "lyrics"
    organize = "organize"


class JobTask(BaseModel):
    id: str
    type: TaskType
    source: str
    target: str
    worker: Optional[str] = None
    status: JobStatus = JobStatus.pending
    output: Optional[str] = None


class Job(BaseModel):
    id: str
    name: str
    tasks: List[JobTask]
    status: JobStatus = JobStatus.pending
    progress: float = 0.0


class WorkerMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    timestamp: str


class WorkerStatus(BaseModel):
    worker_id: str
    active_task: Optional[str] = None
    last_seen: Optional[str] = None
    metrics: Optional[WorkerMetrics] = None


def new_job_id() -> str:
    return str(uuid4())


def new_task_id() -> str:
    return str(uuid4())
