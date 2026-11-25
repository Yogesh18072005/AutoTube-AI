from __future__ import annotations
import os
from celery import Celery

celery_app = Celery("autotube", broker=os.getenv("REDIS_URL","redis://localhost:6379/0"), backend=os.getenv("REDIS_URL","redis://localhost:6379/0"))
celery_app.conf.update(task_track_started=True, task_serializer="json", accept_content=["json"], result_serializer="json", timezone="UTC", enable_utc=True, task_acks_late=True, worker_prefetch_multiplier=1)

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=4)
def execute_pipeline(self, project: dict):
    required=["topic","language","format"]
    missing=[key for key in required if not project.get(key)]
    if missing: raise ValueError("Missing pipeline fields: "+", ".join(missing))
    # Tasks are deliberately stage records until a configured provider adapter is attached.
    return {"job_id":self.request.id,"status":"queued_for_provider","stages":["research","script","voice","visuals","render","thumbnail","seo","human_review"],"approval_required":True,"project":project}
