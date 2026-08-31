import os
from datetime import datetime, timezone
from pathlib import Path

from minio import Minio


def upload_reports(output_dir: Path) -> str | None:
    """Uploads every file under `output_dir` to MinIO, under a timestamped
    prefix so each pipeline run gets its own folder in the bucket.

    No-ops (returns None) when MinIO isn't configured via env vars, so the
    pipeline keeps working standalone with just local output.
    """
    endpoint = os.environ.get('MINIO_ENDPOINT')
    access_key = os.environ.get('MINIO_ACCESS_KEY')
    secret_key = os.environ.get('MINIO_SECRET_KEY')
    bucket = os.environ.get('MINIO_BUCKET', 'tweet-reports')

    if not (endpoint and access_key and secret_key):
        return None

    client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    run_id = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    for path in output_dir.rglob('*'):
        if path.is_file():
            object_name = f'{run_id}/{path.relative_to(output_dir).as_posix()}'
            client.fput_object(bucket, object_name, str(path))

    return run_id
