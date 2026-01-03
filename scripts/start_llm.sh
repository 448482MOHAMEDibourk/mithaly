#!/usr/bin/env bash
set -euo pipefail

# Start the local LLM runtime.
# Usage:
#   ./scripts/start_llm.sh docker       # run via Docker (default image placeholder)
#   ./scripts/start_llm.sh runtime      # run using local runtime binary set in MITHALY_LLM_RUNTIME

: "${MITHALY_MODELS_PATH:=${HOME}/.local/share/mithaly/models}"
: "${MITHALY_LLM_RUNTIME:=}"
: "${LLM_DOCKER_IMAGE:=ollama/ollama:latest}"

MODE="${1:-docker}"

if [ "$MODE" = "docker" ]; then
  echo "Starting LLM in Docker mode..."
  echo "Models path: $MITHALY_MODELS_PATH"
  mkdir -p "$MITHALY_MODELS_PATH"
  docker run --rm -p 127.0.0.1:8080:8080 \
    -v "$MITHALY_MODELS_PATH":/models:ro \
    --name mithaly-llm \
    "$LLM_DOCKER_IMAGE" \
    serve --models /models --host 0.0.0.0 --port 8080
else
  if [ -z "$MITHALY_LLM_RUNTIME" ]; then
    echo "ERROR: MITHALY_LLM_RUNTIME is not set. Set it to your runtime binary path or use docker mode." >&2
    exit 2
  fi
  echo "Starting LLM runtime binary: $MITHALY_LLM_RUNTIME"
  exec "$MITHALY_LLM_RUNTIME" --models "$MITHALY_MODELS_PATH" --host 127.0.0.1 --port 8080
fi
