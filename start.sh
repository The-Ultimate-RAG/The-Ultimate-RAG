#!/usr/bin/env sh
echo "step 0 is ready"
# Load environment variables from .env
export $(grep -v '^#' /app/.env | xargs)
echo "Loaded environment variables from .env"

# Run initializer
python -m app.initializer
echo "step 1 is ready"

# Start Qdrant in the background with fresh storage snapshot directory
rm -rf ./database/*
qdrant --config-path config.yaml &
echo "step 2 is ready"
# Wait for Qdrant
for i in {1..10}; do
  if curl -s http://localhost:6333/healthz | grep -q "ok"; then
    echo "Qdrant is ready!"
    break
  fi
  echo "Waiting for Qdrant..."
  sleep 1
done
echo "step 3 is ready"

python -m app.automigration
echo "step 4 is ready"

# Start the main application in the background
uvicorn app.api.api:api --host 0.0.0.0 --port 7860 &
echo "step 5 is ready"

# Wait for uvicorn
for i in {1..10}; do
  if curl -s http://localhost:7860/health | grep -q "ok"; then
    echo "Uvicorn is ready!"
    break
  fi
  echo "Waiting for uvicorn..."
  sleep 1
done

# Keep container running
tail -f /dev/null
