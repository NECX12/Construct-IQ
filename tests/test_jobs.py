import time

from app.jobs import get_blueprint_job, submit_blueprint_job


def test_blueprint_job_processes_json_fixture_in_background():
    content = b'{"drawing_type":"floor_plan","building_elements":[]}'
    job_id = submit_blueprint_job("sample.json", content)
    deadline = time.monotonic() + 5

    while time.monotonic() < deadline:
        job = get_blueprint_job(job_id)
        if job and job.state not in {"queued", "running"}:
            break
        time.sleep(0.01)

    assert job is not None
    assert job.state == "extracted"
    assert job.extraction is not None
    assert job.extraction.filename == "sample.json"
