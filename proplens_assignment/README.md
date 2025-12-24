# Proplens AI Sales Agent (v2)

This repository contains the solution for the **AI Engineer Challenge v2**. It implements an intelligent Property Sales Agent orchestrated by **LangGraph**, served via a **Django Ninja** API.

## 🏗 Architecture

- **Framework**: Django Ninja (Python)
- **Agent Orchestration**: LangGraph (Router -> Recommender/Detailer/Searcher/Booker)
- **Text-to-SQL**: Vanna AI (trained on SQLite Property schema)
- **Database**: SQLite
  - `agent_property`: Real estate projects/units (imported from CSV).
  - `agent_booking`: Visit bookings.
  - `agent_lead`: Lead information captured during conversation.
- **Tools**:
  - **SQL Tool**: Queries database for recommendations and details.
  - **Web Search**: Fallback for external information (Simulated/Mock in restricted environments, adaptable to DuckDuckGo/Google).
- **LLM**: OpenAI (GPT-3.5-turbo)

## 🚀 Setup & Installation

### Prerequisites
- Python 3.9+
- OpenAI API Key

### 1. Clone & Install Dependencies
```bash
git clone <repo-url>
cd proplens_assignment
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the `proplens_assignment` directory (if not present):
```bash
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_django_secret_key
DEBUG=True
```

### 3. Initialize Database
Run migrations and import the property data:
```bash
python manage.py migrate
python scripts/import_properties.py
```

## 🏃‍♂️ Running the Application

Start the development server:
```bash
python manage.py runserver
```
The API will be available at: **http://127.0.0.1:8000/api**

### Interactive Documentation (Swagger UI)
Visit **http://127.0.0.1:8000/api/docs**

## 🧪 Testing

Run the automated flow simulation:
```bash
python test_agent_flow.py
```

## 🧪 Capabilities & Test Cases

### 1. Greeting & Probing
**Input**: "Hi, I'm looking for a property"
**Response**: Asks for City, Budget, Bedrooms.

### 2. Recommendation (Text-to-SQL)
**Input**: "I want a 2 bedroom apartment in Dubai under 2M"
**Response**: Recommends properties matching criteria from the database.

### 3. Project Details (Q&A)
**Input**: "Tell me more about Sobha Crest"
**Response**: Provides description and amenities from the database.

### 4. External Information (Web Search)
**Input**: "What are the schools near Downtown Dubai?"
**Response**: Uses search tool to find external information not in the DB.

### 5. Booking & Lead Capture
**Input**: "I want to book a visit for Sobha Crest. My name is John, email is john@example.com."
**Response**: Captures lead info into `agent_lead`, creates `agent_booking`, and confirms.

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **POST** | `/api/conversations` | Create a new session ID. |
| **POST** | `/api/agents/chat` | Main chat interface. Payload: `{ "message": "...", "conversation_id": "..." }` |

## ☁️ Deployment
Ready for deployment on Render/Vercel. Ensure `OPENAI_API_KEY` environment variable is set.
