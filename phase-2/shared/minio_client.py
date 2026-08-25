"""
MinIO object storage client for TriNetra Phase 2.
Handles image and document upload/download for the Evidence Service.
"""

import io
import logging
import os
from typing import Optional
from uuid import UUID

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

MINIO_ENDPOINT      = os.getenv("MINIO_ENDPOINT",       "localhost:9000")
MINIO_ACCESS_KEY    = os.getenv("MINIO_ROOT_USER",       "trinetra_minio")
MINIO_SECRET_KEY    = os.getenv("MINIO_ROOT_PASSWORD",   "trinetra_minio_pass")
MINIO_BUCKET        = os.getenv("MINIO_BUCKET_EVIDENCE", "evidence-files")
MINIO_SECURE        = os.getenv("MINIO_SECURE", "false").lower() == "true"


class MinioClient:
    """
    Wrapper around the MinIO Python SDK for evidence file storage.

    Usage:
        client = MinioClient()
        url = client.upload_bytes("claim-id/receipt.jpg", file_bytes, "image/jpeg")
        data = client.download_bytes("claim-id/receipt.jpg")
    """

    def __init__(self) -> None:
        self._client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create the evidence bucket if it does not exist."""
        try:
            if not self._client.bucket_exists(MINIO_BUCKET):
                self._client.make_bucket(MINIO_BUCKET)
                logger.info("Created MinIO bucket: %s", MINIO_BUCKET)
        except S3Error as exc:
            logger.error("Failed to create MinIO bucket: %s", exc)

    def upload_bytes(
        self,
        object_key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload raw bytes to MinIO.
        Returns the public-accessible URL for the stored object.
        """
        stream = io.BytesIO(data)
        self._client.put_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_key,
            data=stream,
            length=len(data),
            content_type=content_type,
        )
        url = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{object_key}"
        logger.info("Uploaded to MinIO: %s", url)
        return url

    def download_bytes(self, object_key: str) -> bytes:
        """Download an object from MinIO and return as raw bytes."""
        response = self._client.get_object(MINIO_BUCKET, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def generate_presigned_url(self, object_key: str, expires_hours: int = 24) -> str:
        """Generate a time-limited pre-signed URL for direct browser access."""
        from datetime import timedelta
        return self._client.presigned_get_object(
            MINIO_BUCKET,
            object_key,
            expires=timedelta(hours=expires_hours),
        )

    def delete_object(self, object_key: str) -> None:
        """Delete an object from MinIO storage."""
        self._client.remove_object(MINIO_BUCKET, object_key)
        logger.info("Deleted from MinIO: %s", object_key)

    def object_key_for_evidence(self, claim_id: UUID, evidence_id: UUID, filename: str) -> str:
        """Generate a structured object key for evidence files."""
        return f"claims/{claim_id}/evidence/{evidence_id}/{filename}"


# ─── Singleton ───────────────────────────────────────────────────────────────
_minio_client: Optional[MinioClient] = None


def get_minio_client() -> MinioClient:
    """Get the shared MinIO client instance (lazy initialization)."""
    global _minio_client
    if _minio_client is None:
        _minio_client = MinioClient()
    return _minio_client
