# Legal Assistant Monolithic Application

This repository contains a monolithic application for a Legal Assistant, featuring an Angular frontend and a FastAPI backend with PostgreSQL and pgvector for database management.

## Project Structure

- `backend/`: FastAPI application
- `frontend/`: Angular application
- `.github/workflows/`: GitHub Actions for CI/CD

## Technologies Used

- **Frontend**: Angular
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Vector Database**: pgvector
- **CI/CD**: GitHub Actions
- **Containerization**: Docker, Docker Compose

## Setup and Development

### Prerequisites

- Docker and Docker Compose
- Node.js and npm (for frontend development)
- Python 3.9+ and pip (for backend development)

### Local Development

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-org/legal-assistant.git
    cd legal-assistant
    ```

2.  **Create `.env` file:**
    Copy the `.env.example` file to `.env` and fill in the necessary environment variables.
    ```bash
    cp .env.example .env
    ```

3.  **Build and run with Docker Compose:**
    ```bash
    docker-compose up --build
    ```
    This will start the PostgreSQL database, FastAPI backend, and Angular frontend.

    -   Frontend will be available at `http://localhost:4200`
    -   Backend will be available at `http://localhost:8000`

### Backend Development (FastAPI)

Navigate to the `backend` directory.

```bash
cd backend
```

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run migrations (using Alembic):**
    ```bash
    # (Initial setup for Alembic will be required)
    alembic upgrade head
    ```

3.  **Run the backend server:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

### Frontend Development (Angular)

Navigate to the `frontend` directory.

```bash
cd frontend
```

1.  **Install dependencies:**
    ```bash
    npm install
    ```

2.  **Run the frontend server:**
    ```bash
    npm start
    ```

## CI/CD

GitHub Actions workflows are located in `.github/workflows/`:

-   `ci.yml`: Continuous Integration (linting, testing)
-   `cd.yml`: Continuous Deployment (build, push to registry, deploy)

---

**Note**: This `README.md` provides a basic structure. You should expand upon each section with more detailed instructions, API documentation, frontend components overview, testing guidelines, and deployment specifics.
