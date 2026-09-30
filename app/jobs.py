from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from threading import Lock
from uuid import uuid4

from .document_processing import pdf_page_count
from .extraction import extract_blueprint
from .models import DrawingExtraction


@dataclass
class BlueprintJob:
    job_id: str
    filename: str
    state: str = "queued"
    message: str = "Waiting to process blueprint..."
    progress: int = 0
    extraction: DrawingExtraction | None = None
    pdf_pages: int | None = None
    error: str | None = None


_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="blueprint")
_jobs: dict[str, BlueprintJob] = {}
_jobs_lock = Lock()


def _update_job(job_id: str, **changes: object) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is not None:
            for key, value in changes.items():
                setattr(job, key, value)


def _process_blueprint(job_id: str, filename: str, content: bytes) -> None:
    try:
        _update_job(job_id, state="running", message="Checking the uploaded file...", progress=10)
        page_count = pdf_page_count(content) if filename.lower().endswith(".pdf") else None
        _update_job(job_id, message="Processing blueprint...", progress=30)
        extraction = extract_blueprint(filename, content)
        _update_job(
            job_id,
            state="extracted",
            message="Finalizing quantities and costs...",
            progress=80,
            extraction=extraction,
            pdf_pages=page_count,
        )
    except Exception as exc:
        _update_job(
            job_id,
            state="failed",
            message="Blueprint processing failed.",
            progress=100,
            error=str(exc),
        )


def submit_blueprint_job(filename: str, content: bytes) -> str:
    job_id = uuid4().hex
    with _jobs_lock:
        _jobs[job_id] = BlueprintJob(job_id=job_id, filename=filename)
    _executor.submit(_process_blueprint, job_id, filename, content)
    return job_id


def get_blueprint_job(job_id: str) -> BlueprintJob | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        return replace(job) if job is not None else None


def mark_blueprint_job_complete(job_id: str) -> None:
    _update_job(job_id, state="complete", message="Blueprint processing complete.", progress=100)


def mark_blueprint_job_failed(job_id: str, error: str) -> None:
    _update_job(job_id, state="failed", message="Blueprint processing failed.", progress=100, error=error)
