FROM python:3.10-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./app /app/app

RUN mkdir -p /app/storage/uploads /app/storage/generated

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
