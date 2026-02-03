# AI Agent Service

A multi-agent AI service built with FastAPI and Google Gemini, featuring A2A (Agent-to-Agent) protocol support.

## Project Structure

```
/
├── main.py                  # Entry point
├── settings.py              # Configuration (reads from .env)
├── requirements.txt         # Python dependencies
├── app/
│   ├── server.py            # FastAPI app setup & route registration
│   ├── routes/              # API endpoints
│   │   ├── route.py
│   ├── agents/              # AI agent implementations
│   │   └── rule_review_agent/
│   │       ├── agent.py         # Core agent logic
│   │       ├── runner.py        # Execution wrapper
│   │       ├── executor.py      # A2A protocol handler
│   │       ├── request_handler.py # A2A app setup
│   │       ├── agent_card.py    # A2A agent metadata
│   │       └── knowledge/
│   │           └── prompts.py   # System prompts
│   ├── services/            # Business logic services
│   ├── controllers/         # Controller layer
│   ├── config/              # DB connections, configs
│   ├── middleware/          # Auth, response wrappers
│   ├── models/              # Data models
│   └── utils/               # Utilities
└── tests/                   # Test files
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your API keys:

```env
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 3. Run the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn app.server:app --reload
```

### 4. Access the API

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Creating a New Agent

To create a new agent, follow this structure:

```
app/agents/my_new_agent/
├── __init__.py
├── agent.py               # Core agent logic
├── runner.py              # Execution wrapper
├── executor.py            # A2A executor (if A2A enabled)
├── request_handler.py     # A2A app setup (if A2A enabled)
├── agent_card.py          # A2A metadata (if A2A enabled)
└── knowledge/
    ├── __init__.py
    └── prompts.py         # System prompts
```

### Agent Components

1. **agent.py**: Contains the core agent logic, LLM integration, and response processing
2. **runner.py**: Wraps the agent with timeout handling, error handling, and batch processing
3. **executor.py**: Handles A2A protocol messages and formats responses
4. **request_handler.py**: Sets up FastAPI endpoints for A2A communication
5. **agent_card.py**: Defines agent metadata for A2A discovery
6. **knowledge/prompts.py**: System prompts and templates

## Running Tests

```bash
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ --cov=app --cov-report=html
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `True` |
| `DEFAULT_MODEL` | Default LLM model | `gemini-2.0-flash` |
| `MAX_AGENT_ITERATIONS` | Max agent iterations | `10` |
| `AGENT_TIMEOUT` | Agent timeout (seconds) | `300` |
| `A2A_ENABLED` | Enable A2A protocol | `True` |

## License

MIT
