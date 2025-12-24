# PropLens Agent

A conversational AI agent for Real Estate, built with Django Ninja, LangGraph, and Vanna.

## Features

- **Natural Language Property Search**: Search for properties using natural language queries (Text-to-SQL).
- **Project Details**: Get specific details about projects from the database.
- **Web Search**: Fallback to web search for general questions or external info (schools, etc.).
- **Booking Flow**: intelligently detects interest and collects lead details for booking.
- **REST API**: Exposes endpoints for chat and conversation management.

## Tech Stack

- **Backend**: Python, Django, Django Ninja Extra (Controller-based).
- **Agent**: LangGraph (State management, routing).
- **Text-to-SQL**: Vanna AI + ChromaDB.
- **Database**: SQLite (Development).

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file (or set env vars) with:
    ```
    OPENAI_API_KEY=sk-...
    TAVILY_API_KEY=tvly-...
    SECRET_KEY=...
    DEBUG=True
    ```

3.  **Migrations**:
    ```bash
    python manage.py migrate
    ```

4.  **Run Server**:
    ```bash
    python manage.py runserver
    ```

## API Documentation

Access the interactive API docs at: `http://localhost:8000/api/docs`

### Endpoints

-   `POST /api/conversations`: Start a new session.
-   `POST /api/agents/chat`: Send a message.
    -   Header: `Authorization: Bearer supersecret`
    -   Body: `{"conversation_id": "...", "message": "..."}`
-   `GET /api/bookings`: List confirmed bookings.

## Testing

Run the test suite:
```bash
python manage.py test agent
```
