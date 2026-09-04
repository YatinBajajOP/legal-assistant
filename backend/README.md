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
    First, you'll need to initialize Alembic if you haven't already. This usually involves:
    ```bash
    alembic init -t async migrations
    # Then, configure alembic.ini and env.py with your DATABASE_URL
    alembic revision --autogenerate -m "Initial migration"
    alembic upgrade head
    ```

5.  **Run the FastAPI application:**
    ```bash
    uvicorn app.main:app --reload
    ```

    The API documentation will be available at `http://localhost:8000/api/v1/docs`.

## Project Structure

-   `app/api/`: API routers and endpoints
-   `app/core/`: Core settings, security, and utilities
-   `app/db/`: Database models, session management
-   `app/schemas/`: Pydantic models for request/response validation
-   `app/services/`: Business logic and CRUD operations
-   `migrations/`: Alembic migration scripts
-   `requirements.txt`: Python dependencies
-   `Dockerfile`: Dockerfile for containerization
-   `.env.example`: Example environment variables
