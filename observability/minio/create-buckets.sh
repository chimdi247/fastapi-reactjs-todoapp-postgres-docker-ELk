#!/bin/sh
# One-shot job (minio/mc image): creates every bucket the observability stack
# needs. Idempotent. Replace MinIO with real S3 and these become plain `aws s3 mb`.
set -eu

until mc alias set local "http://minio:9000" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
  echo "waiting for minio..."; sleep 2
done

for bucket in "$MIMIR_BLOCKS_BUCKET" "$MIMIR_RULER_BUCKET" "$MIMIR_ALERTMANAGER_BUCKET" "$ES_SNAPSHOT_BUCKET"; do
  mc mb --ignore-existing "local/$bucket"
done

# Log archive: expire snapshot objects Elasticsearch no longer references after
# 90 days as a safety net (SLM retention normally removes them sooner).
mc ilm rule add --expire-days 90 "local/$ES_SNAPSHOT_BUCKET" 2>/dev/null || true

echo "buckets ready:"; mc ls local
