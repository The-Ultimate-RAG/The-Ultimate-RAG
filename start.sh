#!/usr/bin/env sh
echo "step 0 is ready"
# Run initializer and wait for it to complete
python -m app.initializer
echo "step 1 is ready"

# Start Qdrant in the background with fresh storage snapshot directory
rm -rf ./database/*  # Clear old data
qdrant --config-path config.yaml &
echo "step 2 is ready"
# Wait longer for Qdrant to spin up
sleep 1
echo "step 3 is ready"

python -m app.automigration
echo "step 4 is ready"
# Start the main application
uvicorn app.api:api --host 0.0.0.0 --port 7860
#python -m app.main
echo "step 5 is ready"