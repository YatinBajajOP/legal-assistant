# FastAPI Backend for Legal Assistant

This directory contains the FastAPI backend application for the Legal Assistant project.

## Features

- RESTful API endpoints
- PostgreSQL database integration with SQLAlchemy
- pgvector for vector embeddings
- Alembic for database migrations
- Pydantic for data validation and serialization
- JWT for authentication (example structure)

## Development

Refer to the main `README.md` in the project root for overall setup instructions.

### Running Locally (without Docker Compose)

1.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    ./venv/Scripts/activate # On Windows
    source venv/bin/activate # On macOS/Linux
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Copy `.env.example` to `.env` and fill in your database credentials and secret keys.
    ```bash
    cp .env.example .env
    ```

4.  **Run database migrations (Alembic):**
    Alembic is already initialized (`alembic.ini`, `migrations/env.py`, `migrations/versions/0001_initial.py`).
    Ensure PostgreSQL is running with the `vector` extension available (the bundled
    `pgvector/pgvector:pg16` Docker image already provides it), then run:
    ```bash
    alembic upgrade head
    ```
    To create a new migration after changing models:
    ```bash
    alembic revision --autogenerate -m "describe change"
    alembic upgrade head
    ```

5.  **Run the FastAPI application:**
    ```bash
    uvicorn app.main:app --reload
    ```

    The API documentation will be available at `http://localhost:8000/api/v1/docs`.

## Resolution Plan Creator backend

Implements the full pipeline: upload -> extract/chunk -> embed -> pgvector store ->
RAG-based template question answering -> populated JSON -> DOCX export.

Endpoints (under `/api/v1/resolution-plan`):

-   `POST /documents` — upload a source document (PDF/DOCX/TXT). Returns immediately;
    extraction/chunking/embedding runs in the background. Poll `GET /documents/{id}`.
-   `GET /documents` — list uploaded documents for the current (mock) user.
-   `GET /documents/{id}` — check a document's processing status.
-   `POST /generations` — start generating the Resolution Plan review from a set of
    fully-processed `document_ids`. Runs the RAG/LLM pipeline in the background.
-   `GET /generations/{id}` — poll generation status; once `completed`, includes the
    populated template JSON.
-   `GET /generations/{id}/download` — download the generated `.docx` once `completed`.

Template resources are bundled at `app/resources/resolution_plan/` and the DOCX writer
(`app/services/resolution_plan/generator.py`) is reused unmodified from
`reference_data/AI - Resolution Plan/resolution_plan_generator.py`.

Authentication is not implemented yet: all requests operate against a single
static/mock user (seeded on startup from `MOCK_USER_EMAIL`).

## Project Structure

-   `app/api/`: API routers and endpoints
-   `app/core/`: Core settings, security, and utilities
-   `app/db/`: Database models, session management
-   `app/schemas/`: Pydantic models for request/response validation
-   `app/repositories/`: Data-access layer (DB queries only)
-   `app/services/`: Business logic — ingestion (extraction/chunking), embeddings,
    LLM orchestration, and resolution-plan generation
-   `migrations/`: Alembic migration scripts
-   `requirements.txt`: Python dependencies
-   `Dockerfile`: Dockerfile for containerization
-   `.env.example`: Example environment variables
