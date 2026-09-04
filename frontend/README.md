# Angular Frontend for Legal Assistant

This directory contains the Angular frontend application for the Legal Assistant project.

## Features

- User interface for interacting with the Legal Assistant backend.
- Angular routing, components, and services.
- Environment-specific configurations.

## Development

Refer to the main `README.md` in the project root for overall setup instructions.

### Running Locally (without Docker Compose)

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Set up environment variables:**
    If you need to override environment variables for local development, create a `.env` file from `.env.example`.
    ```bash
    cp .env.example .env
    ```

4.  **Run the Angular development server:**
    ```bash
    npm start
    ```

    The application will be served at `http://localhost:4200`.

## Project Structure

-   `src/app/`: Main application components, modules, and services.
-   `src/environments/`: Environment-specific configuration files.
-   `src/assets/`: Static assets like images.
-   `angular.json`: Angular CLI configuration.
-   `package.json`: Frontend dependencies and scripts.
-   `tsconfig.json`: TypeScript configuration.
