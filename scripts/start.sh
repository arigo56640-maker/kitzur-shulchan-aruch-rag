#!/usr/bin/env bash
# Railway start command. Builds the Chroma index on first boot (one-time, takes
# ~1 min and ~$0.01 in OpenAI embeddings), then launches Chainlit bound to $PORT.
# The chroma_db/ directory is expected to be a Railway volume so this only
# runs once per service lifetime.
set -euo pipefail

CHROMA_SQLITE="${CHROMA_DIR:-/app/chroma_db}/chroma.sqlite3"

if [ ! -f "$CHROMA_SQLITE" ]; then
  echo "[start] No chroma index at $CHROMA_SQLITE — building now (one-time)..."
  python backend/scripts/build_index.py
else
  echo "[start] Chroma index found at $CHROMA_SQLITE — skipping build."
fi

cd frontend
exec chainlit run src/kitzur_chat/app.py \
  --headless \
  --host 0.0.0.0 \
  --port "${PORT:-8000}"
