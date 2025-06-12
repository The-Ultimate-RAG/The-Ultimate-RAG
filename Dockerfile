FROM python:3.11-slim-bookworm

LABEL authors="user"

# Set environment variables for non-buffered Python output and no bytecode generation
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies and clean up
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY ./app/requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./app /app

# Expose the port your FastAPI application listens on
EXPOSE 5050

CMD ["python", "-m", "uvicorn", "api:api", "--host", "0.0.0.0", "--port", "5050"]
