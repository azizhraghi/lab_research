#!/bin/bash
# Run database migrations
alembic upgrade head

# Start the FastAPI application
uvicorn api.main:app --host 0.0.0.0 --port $PORT
