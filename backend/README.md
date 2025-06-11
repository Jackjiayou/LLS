# FastAPI Backend Project

This directory contains the backend for the project, built with FastAPI.

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── items.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── core/
│   │   └── __init__.py
│   ├── db/
│   │   └── __init__.py
│   ├── models/
│   │   └── __init__.py
│   ├── schemas/
│   │   └── __init__.py
│   └── __init__.py
├── main.py
├── requirements.txt
└── README.md
```

- `main.py`: The main FastAPI application file.
- `requirements.txt`: Python dependencies for the project.
- `app/`: Contains the core logic of the application.
    - `api/`: API related modules.
        - `endpoints/`: Individual API endpoint definitions (e.g., `items.py`).
    - `core/`: Core configurations, settings, and utilities.
    - `db/`: Database related configurations and session management.
    - `models/`: SQLAlchemy models (if using an ORM).
    - `schemas/`: Pydantic schemas for request and response data validation.

## Getting Started

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    -   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    -   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the application:**
    ```bash
    uvicorn main:app --reload
    ```

The API will be accessible at `http://127.0.0.1:8000`. You can access the API documentation at `http://127.0.0.1:8000/docs` (Swagger UI) or `http://127.0.0.1:8000/redoc` (ReDoc). 