# Eshtri Aqar Chatbot

AI-powered real estate chatbot with RAG (Retrieval Augmented Generation) and SQL query capabilities for property search and policy information.

## Features

- 🏠 **Property Search**: Natural language property search with SQL query generation
- 📚 **Policy Q&A**: RAG-based answers from policy documents
- 💬 **Chat Interface**: Premium UI with chat history and session management
- 📊 **SQL Logs**: Real-time SQL query execution logs
- 🔒 **Safety Guard**: Content filtering for safe interactions
- 🌐 **Multi-language**: Support for English and Arabic

## Tech Stack

- **Backend**: FastAPI, LangChain, OpenAI GPT-4
- **Database**: MySQL
- **Vector Store**: ChromaDB with HuggingFace embeddings
- **Frontend**: Vanilla JavaScript with premium UI design

## Local Development

### Prerequisites

- Python 3.10+
- MySQL database access
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd eshtri-aqar-chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```env
   OPENAI_API_KEY=sk-...
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=your_db_host
   DB_PORT=31306
   DB_NAME=eshtri
   ```

4. **Prepare RAG database** (first time only)
   
   The application will automatically build the RAG database from files in the `data/` directory on first run. Ensure your policy documents are in `data/`:
   - `data/policy.txt`
   - `data/taalat_mostafa_policy.pdf`

5. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```

6. **Open in browser**
   ```
   http://localhost:8000
   ```

## Deployment to Render

### Option 1: Using Render Dashboard

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo>
   git push -u origin main
   ```

2. **Create new Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: eshtri-aqar-chatbot
     - **Environment**: Python
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Add Environment Variables**
   
   In Render dashboard, add these environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `DB_USER`: Database username
   - `DB_PASSWORD`: Database password
   - `DB_HOST`: Database host
   - `DB_PORT`: 31306
   - `DB_NAME`: eshtri

4. **Deploy**
   
   Render will automatically deploy your application.

### Option 2: Using render.yaml

The repository includes a `render.yaml` file for infrastructure-as-code deployment:

1. Push code to GitHub
2. In Render dashboard, click "New +" → "Blueprint"
3. Connect your repository
4. Render will read `render.yaml` and create the service
5. Add environment variables in the dashboard

## API Documentation

### Endpoints

#### `POST /api/chat`
Process chat message and return response.

**Request:**
```json
{
  "message": "Show me 3 bedroom apartments",
  "session_id": "user-123"
}
```

**Response:**
```json
{
  "response": "Here are some 3 bedroom apartments...",
  "sql_logs": [
    {
      "query_name": "Property Search",
      "sql": "SELECT * FROM unit_search_sorting WHERE room = 3 AND lang_id = 1 LIMIT 5;",
      "success": true,
      "row_count": 5,
      "error": null
    }
  ]
}
```

#### `GET /health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "service": "Eshtri Aqar Chatbot",
  "version": "1.0.0"
}
```

#### `POST /api/clear-session`
Clear chat session.

#### `GET /api/test-db`
Test database connection.

## Project Structure

```
eshtri-aqar-chatbot/
├── main.py                 # FastAPI application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment config
├── .env.example          # Environment variables template
├── services/
│   ├── rag_service.py    # RAG document processing & search
│   ├── database_service.py # MySQL operations
│   ├── agent_service.py  # LangChain agent & tools
│   └── chat_service.py   # Chat orchestration
├── static/
│   ├── index.html        # Frontend UI
│   ├── style.css         # Styles
│   ├── script.js         # Frontend logic
│   └── favicon.svg       # Icon
└── data/
    ├── policy.txt        # Policy document
    └── taalat_mostafa_policy.pdf # PDF policy
```

## Troubleshooting

### RAG Database Issues

If the RAG database fails to load:
1. Delete the `rag_db/` directory
2. Ensure policy files are in `data/` directory
3. Restart the application - it will rebuild automatically

### Database Connection Issues

1. Verify credentials in `.env` file
2. Test connection: `curl http://localhost:8000/api/test-db`
3. Check database firewall allows connections from your IP

### OpenAI API Issues

1. Verify API key is correct
2. Check API quota and billing
3. Ensure API key has access to `gpt-4o-mini` model

## License

MIT

## Support

For issues and questions, please open a GitHub issue.
