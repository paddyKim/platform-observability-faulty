#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://localhost:8102}"
REQUESTS="${REQUESTS:-120}"
CONCURRENCY="${CONCURRENCY:-10}"

seq "$REQUESTS" | xargs -P "$CONCURRENCY" -I {} sh -c '
  curl --silent --output /dev/null --write-out "%{http_code}\n" "$1/api/orders/$2"
' _ "$BASE_URL" {}

echo "Generated $REQUESTS intentionally failing requests against $BASE_URL"
