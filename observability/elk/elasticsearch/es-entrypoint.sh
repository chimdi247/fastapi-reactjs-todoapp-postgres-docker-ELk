#!/usr/bin/env bash
# Wraps the stock Elasticsearch entrypoint to put the S3 credentials into the
# keystore (the only supported place for repository-s3 secrets), then hands over.
set -euo pipefail

KEYSTORE=/usr/share/elasticsearch/config/elasticsearch.keystore

[[ -f "$KEYSTORE" ]] || elasticsearch-keystore create

printf '%s' "${S3_ACCESS_KEY:?S3_ACCESS_KEY is required}" \
  | elasticsearch-keystore add --stdin --force s3.client.default.access_key
printf '%s' "${S3_SECRET_KEY:?S3_SECRET_KEY is required}" \
  | elasticsearch-keystore add --stdin --force s3.client.default.secret_key

# Same command the image runs by default (ENTRYPOINT + CMD).
exec /bin/tini -- /usr/local/bin/docker-entrypoint.sh eswrapper
