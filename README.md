HCP CRM AI Assistant is An intelligent, Agentic CRM system for Healthcare Professionals (HCPs). This application automates the process of logging interactions, updating historical data, and providing strategic insights using a LangGraph orchestration backend and a React frontend.🚀 OverviewThis project transforms traditional CRM data entry into a conversational experience. Using Large Language Models (LLMs), the system "thinks" before it acts—determining whether to create a new log, update an existing one, or pull historical insights based on the conversation context.Key CapabilitiesSmart Logging: Automatically extracts doctor names, topics, and sentiments.Intelligent Deduplication: Prevents duplicate entries through AI logic and database constraints.Strategic Insights: Suggests next-action recommendations (e.g., "Pitch advanced benefits").Real-time Sync: The UI Sidebar and Chat refresh instantly as the database changes.🛠️ Tech StackFrontend: React.js, Tailwind CSSBackend: Python 3.10+, FastAPIAI Orchestration: LangChain & LangGraphLLM: Llama 3.1-70B (via Groq)Database: PostgreSQLConcurrency: Uvicorn (ASGI Server)📂 Project StructurePlaintexthcp-crm-ai/
├── backend/
│   ├── agent.py         # LangGraph workflow & Tool definitions
│   ├── database.py      # PostgreSQL CRUD & Connection logic
│   ├── main.py          # FastAPI endpoints & Session management
│   └── .env             # API Keys (Groq)
├── frontend/
│   ├── src/
│   │   ├── components/  # Chat interface & Sidebar
│   │   └── App.js       # Main Frontend Logic
│   ├── package.json     # Node dependencies
│   └── public/
└── README.md            # Project Documentation
⚙️ Installation & Setup1. Database ConfigurationCreate a PostgreSQL database named hcp_crm_db and execute the following schema:SQLCREATE TABLE hcp_interactions (
    id SERIAL PRIMARY KEY,
    doctor_name VARCHAR(255) NOT NULL,
    topic VARCHAR(255),
    raw_summary TEXT,
    sentiment VARCHAR(50),
    interaction_type VARCHAR(100),
    materials_shared TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE follow_ups (
    id SERIAL PRIMARY KEY,
    doctor_name VARCHAR(255),
    followup_date DATE,
    purpose TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
2. Backend SetupBashcd backend
pip install fastapi uvicorn langchain-groq langgraph psycopg2-binary python-dotenv
# Create a .env file and add: GROQ_API_KEY=your_key_here
python main.py
3. Frontend SetupBashcd frontend
npm install
npm start
The application will be live at http://localhost:3000.📡 API Reference (Backend)MethodEndpointDescriptionPOST/log-interactionProcesses user chat and triggers AI Agent logic.GET/get-logsFetches the full history for the UI Sidebar.POST/reset-session/{id}Clears AI short-term memory for a specific user.GET/debug/session/{id}Inspects the current state of the AI conversation.🛡️ Production FeaturesResponse Merging: The system merges ToolMessage data (technical results) with AIMessage content (natural language) to ensure the UI never misses a "correct answer."DB Deduplication: A 10-second interval check in the database layer prevents accidental double-saves of the same meeting.Stateful Memory: The AI remembers doctors mentioned earlier in the session to decide between "Save" and "Update."
