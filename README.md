# Front Desk - Personal Assistant Agent System

A LangChain/LangGraph-based personal assistant agent with comprehensive Google Calendar, Gmail, and filesystem access. Built with intelligent middleware for date context awareness and human-in-the-loop safety controls.

## Overview

Front Desk provides a conversational AI assistant that can help you manage your calendar, emails, and files through natural language. The agent uses the [common_tools](https://github.com/danielgshea/common_tools) repository for integrated Google Workspace and filesystem capabilities.

### Key Features

- 🗓️ **Google Calendar Integration**: View, create, update, and delete calendar events
- 📧 **Gmail Integration**: Read, send, reply to emails, search messages, and manage labels (14 tools available)
- 📁 **Filesystem Operations**: Create, read, write, delete, and list files with safety controls
- 🤖 **Smart Date Handling**: Automatic date context injection for accurate relative date parsing
- 🛡️ **Human-in-the-Loop**: Approval workflow for destructive operations on calendar, email, and filesystem
- 📊 **LangSmith Tracing**: Full observability of agent interactions and tool calls
- 🔄 **Persistent Memory**: Conversation history with LangGraph checkpointing
- 🎯 **Flexible LLM Support**: Works with OpenRouter (Claude) or local models via LM Studio

## Architecture

- **Agent Framework**: LangGraph with LangChain tools
- **Checkpointing**: In-memory state management for conversation continuity
- **Middleware Stack**:
  - Date Context Middleware: Injects current date/time for accurate scheduling
  - Human-in-the-Loop Middleware: Requires approval for destructive operations
- **Tools**: Common Tools repository (integrated as submodule/subdirectory)

## Prerequisites

- **Python 3.13+** (uses Python 3.13 features)
- **Google Cloud Project** with Calendar API and Gmail API enabled
- **OAuth 2.0 credentials** from Google Cloud Console (see [Setup Google APIs](#setup-google-apis))
- **LLM Backend**: Either OpenRouter API key OR LM Studio running locally

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/danielgshea/front-desk.git
cd front-desk
```

### 2. Install Dependencies

This project uses `uv` for dependency management:

```bash
uv sync
```

Alternatively with pip:

```bash
pip install -e .
```

### 3. Setup Google APIs

The agent uses Google Calendar and Gmail APIs via the common_tools repository.

#### Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the required APIs:
   - Navigate to **APIs & Services** > **Library**
   - Search for and enable:
     - **Google Calendar API**
     - **Gmail API**

#### Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Choose **Desktop app** as the application type
4. Download the credentials file
5. **Rename it to `credentials.json`**
6. **Store it in a secure location outside your project directory** (recommended)

**Recommended: Use Environment Variable**

Store your credentials outside the project and reference them via environment variable:

```bash
# Store credentials in a secure location
mkdir -p ~/.config/google
mv ~/Downloads/credentials.json ~/.config/google/credentials.json

# Add to your .env file
echo "GOOGLE_CREDENTIALS_PATH=$HOME/.config/google/credentials.json" >> .env
```

**Alternative: Project Directory**

If you prefer to keep credentials in the project (they're excluded by `.gitignore`):

```
front-desk/
├── credentials.json  ← Place here
├── common_tools/
├── admin_agent/
└── ...
```

**Note**: The same `credentials.json` works for both Gmail and Calendar APIs. The common_tools library will automatically search for credentials in this order:
1. Path specified in `GOOGLE_CREDENTIALS_PATH` environment variable (**recommended**)
2. Current project directory
3. Parent directories (up to 5 levels)

#### Verify Credentials

You can verify your setup using the common_tools utility:

```bash
cd common_tools
python -m utils.verify_credentials
```

### 4. Configure Environment Variables

Create a `.env` file in the project root (use `.env.example` as a template):

```bash
# Google API Credentials (Recommended: use environment variable)
GOOGLE_CREDENTIALS_PATH=/path/to/your/credentials.json

# LangSmith Tracing (optional but recommended)
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_TRACING=true
LANGCHAIN_PROJECT=front-desk

# Option 1: Use OpenRouter with Claude
OPEN_ROUTER_API_KEY=your_openrouter_api_key

# Option 2: Use Local LM Studio
LM_STUDIO_BASE_URL=http://127.0.0.1:1234
LM_STUDIO_MODEL=your-model-name
```

**Note**: Edit `admin_agent/agent.py` to uncomment your preferred LLM backend (OpenRouter or LM Studio).

### 5. First Run Authentication

On first use, the agent will:
1. Open your browser for Google OAuth authentication
2. Request access to your Calendar and Gmail
3. Save tokens securely in `common_tools/token.json`
4. Automatically refresh tokens when needed

## Usage

### Interactive Demo (Recommended)

Run the interactive CLI demo for an easy conversational interface:

```bash
python demo.py
```

This provides a chat-style interface where you can ask the agent to:
- "What events do I have this week?"
- "Schedule a team meeting tomorrow at 2pm for 1 hour"
- "Send an email to john@example.com about the project update"
- "List all unread emails from last week"
- "Create a file called notes.txt with my meeting notes"

### LangGraph Server

Start the agent as a server using LangGraph CLI:

```bash
uv run langgraph dev
```

This will:
- Start a local server on port 8123
- Enable LangGraph Studio interface
- Support HTTP API access
- Enable streaming responses

You can then interact via:
- **LangGraph Studio**: Visual interface for graph execution
- **HTTP API**: REST endpoints for integration
- **Python SDK**: LangGraph client for programmatic access

### Programmatic Usage

```python
import asyncio
from admin_agent import AdminAgent

async def main():
    agent = AdminAgent()
    
    # Calendar operations
    response = await agent.agent.ainvoke(
        {"messages": [{"role": "user", "content": "What's on my calendar this week?"}]},
        {"configurable": {"thread_id": "user_123"}}
    )
    print(response['messages'][-1].content)
    
    # Email operations
    response = await agent.agent.ainvoke(
        {"messages": [{"role": "user", "content": "Show me unread emails from yesterday"}]},
        {"configurable": {"thread_id": "user_123"}}
    )
    print(response['messages'][-1].content)
    
    # File operations (will request approval)
    response = await agent.agent.ainvoke(
        {"messages": [{"role": "user", "content": "Create a file report.txt with today's summary"}]},
        {"configurable": {"thread_id": "user_123"}}
    )
    print(response['messages'][-1].content)

asyncio.run(main())
```

### Direct Execution

You can also run the agent module directly:

```bash
python -m admin_agent.agent
```

## Agent Capabilities

### Google Calendar Tools

- `list_calendars` - View all available Google calendars
- `list_events` - Show upcoming events with flexible filtering
- `create_event` - Add new calendar events with details (location, attendees, etc.)
- `update_event` - Modify existing events
- `delete_event` - Remove events from calendar

### Gmail Tools (14 Available)

- `search_messages` - Search with Gmail query syntax (e.g., "from:boss@company.com is:unread")
- `get_message` - Read full message content
- `send_message` - Send new emails
- `reply_to_message` - Reply to existing threads
- `create_draft` - Create email drafts
- `send_draft` - Send saved drafts
- `list_labels` - Get all Gmail labels
- `add_labels` - Add labels to messages
- `remove_labels` - Remove labels from messages
- `mark_as_read` / `mark_as_unread` - Update read status
- `trash_message` / `untrash_message` - Manage trash
- `get_thread` - Read entire email thread

### Filesystem Tools

- `create_file` - Create new files with content
- `read_file` - Read file contents
- `write_file` - Write/overwrite file contents
- `delete_file` - Delete files (with approval)
- `list_files` - List files with pattern matching

## Intelligent Features

### Date Context Awareness

The agent automatically understands relative dates like:
- "this weekend"
- "next Friday"
- "April 9-12"
- "tomorrow at 2pm"
- "this Monday"

The DateContextMiddleware injects current date/time context into every request, ensuring accurate date calculations.

### Human-in-the-Loop Safety

Destructive operations require human approval:
- Creating, updating, or deleting calendar events
- Sending, replying, or deleting emails
- Creating, writing, or deleting files

Safe read-only operations are auto-approved:
- Listing calendars/events
- Reading emails
- Searching messages
- Reading files
- Listing files

When the agent attempts a destructive action, it will pause and request approval before proceeding.

## Common Tools Integration

This project uses the [common_tools](https://github.com/danielgshea/common_tools) repository, which provides:

- **Modular Design**: Easy-to-use clients for Google Calendar, Gmail, and filesystem operations
- **LangChain Tool Wrappers**: Pre-built tools that integrate seamlessly with LangChain agents
- **Flexible Authentication**: Multiple credential discovery methods
- **Comprehensive Documentation**: Detailed API documentation and examples
- **Active Development**: Regular updates and new features

The common_tools repository is included as a subdirectory and provides the underlying API clients and tool definitions that power the Front Desk agent.

## Project Structure

```
front-desk/
├── admin_agent/              # Main agent implementation
│   ├── agent.py              # Agent initialization, middleware, tools
│   ├── utils/
│   │   └── state.py          # State management utilities
│   └── __init__.py
├── common_tools/             # External tools repository (cloned)
│   ├── gcalendar/            # Google Calendar client & tools
│   ├── gmail/                # Gmail client & tools (14 tools)
│   ├── filesystem/           # Filesystem client & tools
│   ├── utils/                # Credential management
│   └── examples/             # Usage examples
├── demo.py                   # Interactive CLI demo
├── main.py                   # Entry point
├── langgraph.json            # LangGraph configuration
├── pyproject.toml            # Project dependencies
├── .env.example              # Environment template
├── credentials.json          # Google OAuth credentials (not in repo)
└── README.md                 # This file
```

## Configuration

### Switching LLM Backends

Edit `admin_agent/agent.py` to choose your LLM:

**Option 1: OpenRouter with Claude (default)**
```python
self.model = ChatOpenAI(
    model="anthropic/claude-3.7-sonnet",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    temperature=0.7,
)
```

**Option 2: Local LM Studio**
```python
base_url = os.getenv('LM_STUDIO_BASE_URL', 'http://127.0.0.1:1234')
if not base_url.endswith('/v1'):
    base_url = f"{base_url}/v1"

self.model = ChatOpenAI(
    model=os.getenv('LM_STUDIO_MODEL'),
    openai_api_base=base_url,
    openai_api_key="not-needed"
)
```

### Customizing Tools

To modify which tools are available, edit the imports in `admin_agent/agent.py`:

```python
from common_tools.gcalendar.tools import CALENDAR_TOOLS, CALENDAR_TOOLS_D
from common_tools.gmail.tools import GMAIL_TOOLS, GMAIL_TOOLS_D
from common_tools.filesystem.tools import FILE_SYSTEM_TOOLS, FILE_SYSTEM_TOOLS_D

# Combine tools as needed
ALL_TOOLS = CALENDAR_TOOLS + GMAIL_TOOLS + FILE_SYSTEM_TOOLS
UNSAFE_TOOLS = CALENDAR_TOOLS_D + GMAIL_TOOLS_D + FILE_SYSTEM_TOOLS_D
```

## LangSmith Monitoring

All agent interactions are automatically traced in LangSmith when configured:

- **View traces at**: https://smith.langchain.com
- **Project**: `front-desk` (configurable in `.env`)
- **Insights**: See tool usage, latency, token consumption, and errors

## Security Considerations

⚠️ **Never commit sensitive files to version control!**

- `credentials.json` - Google OAuth credentials
- `token.json` - Google authentication tokens  
- `.env` - API keys and configuration

These files are excluded via `.gitignore`, but always double-check before pushing.

### Best Practices for Credentials

**Recommended Approach:**
1. **Store credentials outside your project directory** using `GOOGLE_CREDENTIALS_PATH` environment variable
2. Set restrictive file permissions: `chmod 600 ~/.config/google/credentials.json`
3. Never commit `.env` files containing paths or keys
4. Use different credentials for development vs production

**Example secure setup:**
```bash
# Store credentials securely
mkdir -p ~/.config/google
chmod 700 ~/.config/google
mv credentials.json ~/.config/google/
chmod 600 ~/.config/google/credentials.json

# Add to .env
echo "GOOGLE_CREDENTIALS_PATH=$HOME/.config/google/credentials.json" >> .env
```

This keeps sensitive credentials out of your project directory entirely, reducing the risk of accidental commits or exposure.

### File Safety

The filesystem tools are designed with safety in mind:
- Destructive operations require human approval by default
- Base path restrictions prevent access outside designated directories
- Comprehensive error handling and validation

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agent.py

# Run with verbose output
pytest -v
```

### Dependencies

Managed via `pyproject.toml`:
- `langchain` - Agent framework
- `langchain-openai` - LLM integration
- `langgraph-cli` - Server and development tools  
- `google-api-python-client` - Google API access
- `google-auth-*` - Authentication libraries
- `python-dotenv` - Environment configuration

## Troubleshooting

### "Permission denied" or "Credentials not found"

Ensure your `GOOGLE_CREDENTIALS_PATH` environment variable is set correctly, or that `credentials.json` is in the project root. Verify you've completed the OAuth flow. Run the credential verification tool:

```bash
cd common_tools
python -m utils.verify_credentials
```

### "Token expired" errors

Delete `common_tools/token.json` and re-authenticate on next run.

### LM Studio connection issues

Ensure LM Studio is running and the base URL in `.env` matches its server address (default: `http://127.0.0.1:1234`).

### Human-in-the-Loop not triggering

Verify that the tool names in `UNSAFE_TOOLS` match the actual tool function names and middleware is properly configured.

## Contributing

This is a personal project, but contributions and suggestions are welcome! Feel free to:
- Open issues for bugs or feature requests
- Submit pull requests for improvements
- Fork and adapt for your own use

## Related Projects

- **[common_tools](https://github.com/danielgshea/common_tools)** - The underlying tool suite for Google Calendar, Gmail, and filesystem operations

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built with:
- [LangChain](https://www.langchain.com/) - Agent framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Graph-based orchestration
- [Google APIs](https://developers.google.com/) - Calendar and Gmail integration
