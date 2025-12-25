# PropLens AI Sales Agent

An intelligent Property Sales Agent orchestrated by **LangGraph**, served via a **Django Ninja** API. This agent helps users find properties using natural language, provides detailed project information, and collects lead details for bookings.

## 🏗 Architecture

- **Framework**: Django Ninja (Python)
- **Agent Orchestration**: LangGraph (Router -> Recommender/Detailer/Searcher/Booker)
- **Text-to-SQL**: Vanna AI (trained on SQLite Property schema)
- **Database**: SQLite
  - `agent_property`: Real estate projects/units (imported from CSV).
  - `agent_booking`: Visit bookings.
  - `agent_lead`: Lead information captured during conversation.
  - `agent_message`: Chat history.
- **Tools**:
  - **SQL Tool**: Queries database for recommendations and details.
  - **Web Search**: Fallback for external information (using Tavily).
- **LLM**: OpenAI (GPT-4o)

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
Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY=your_openai_api_key_here
# Optional: Override Tavily API Key if needed
# TAVILY_API_KEY=your_tavily_api_key
SECRET_KEY=your_django_secret_key
DEBUG=True
```

### 3. Initialize Database
Run migrations and import the property data:
```bash
python manage.py migrate
python scripts/import_properties.py
```

### 4. Train Agent (Vanna Setup)
Initialize the Vanna AI training data (DDL, documentation, and SQL examples):
```bash
python manage.py train_agent
```
*Note: This step is crucial for the text-to-SQL functionality to work correctly, especially for specialized queries like "designed by MDC Investments".*

## 🏃‍♂️ Running the Application

Start the development server:
```bash
python manage.py runserver
```
The API will be available at: **http://127.0.0.1:8000/api**

### Interactive Documentation (Swagger UI)
Visit **http://127.0.0.1:8000/api/docs** to test endpoints directly.

## 📡 API Endpoints

### Agents
**POST** `/api/agents/chat`
- **Description**: Main chat interface for the agent.
- **Headers**: `Authorization: Bearer supersecret`
- **Payload**:
  ```json
  {
    "conversation_id": "unique-uuid-string",
    "message": "I want a 2 bedroom apartment in Dubai under 2M"
  }
  ```

### General
**POST** `/api/conversations`
- **Description**: Create a new session ID.

**GET** `/api/bookings`
- **Description**: List all confirmed bookings.

## 🧪 Testing

### Automated Flow Test
Run the simulation script to verify the full agent conversation flow:
```bash
python test_agent_flow.py
```

### Unit Tests
Run the Django test suite:
```bash
python manage.py test agent
```

## 🧪 Capabilities & Examples

### 1. Greeting & Probing
**Input**: "Hi, I'm looking for a property"
**Response**: Asks for City, Budget, Bedrooms.

### 2. Recommendation (Text-to-SQL)
**Input**: "I want a 2 bedroom apartment in Dubai under 2M"
**Response**: Recommends properties matching criteria from the database.
*Note: Large result sets are automatically truncated to prevent context overflow.*

### 3. Developer/Designer Search
**Input**: "Show me properties designed by MDC Investments LLC"
**Response**: Searches specific developer columns to find matches.

### 4. Project Details (Q&A)
**Input**: "Tell me more about Sobha Crest"
**Response**: Provides description and amenities from the database.

### 5. External Information (Web Search)
**Input**: "What are the schools near Downtown Dubai?"
**Response**: Uses search tool to find external information not in the DB.

### 6. Booking & Lead Capture
**Input**: "I want to book a visit for Sobha Crest. My name is John, email is john@example.com."
**Response**: Captures lead info, creates a booking, and confirms.
