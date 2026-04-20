# Front Desk - Personal Assistant Agents

A LangChain-based application hosting personal assistant agents with Google Calendar integration via MCP (Model Context Protocol).

## Features

- **Admin Agent**: Personal assistant with full Google Calendar access
- **LangSmith Tracing**: Automatic logging and monitoring of agent interactions
- **Common Tools**: Access to a tool suite with calendar, email, and filesystem capabilities [Common Tools](https://github.com/danielgshea/common_tools)

## Setup

### Prerequisites

- Python 3.9+
- Node.js 16+ (for MCP servers)
- Google Cloud account with Calendar API enabled

### Installation

**Use uv:**
```
uv sync
```

## Usage

### Run with LangGraph CLI (Recommended)

Start the agent as a server using LangGraph CLI:

```bash
uv run langgraph dev
```

This will:
- Install LangGraph CLI if needed
- Start a server
- Enable LangSmith tracing
- Support the LangGraph Studio interface

You can then interact with the agent via:
- **LangGraph Studio** (visual interface)
- **HTTP API** 
- **Python SDK** using LangGraph client

### Programmatic Usage

```python
import asyncio
from admin_agent import AdminAgent

async def main():
    agent = AdminAgent()
    
    # Ask about upcoming events
    response = await agent.ainvoke(
        "What events do I have this week?"
    )
    print(response['output'])
    
    # Create a new event
    response = await agent.ainvoke(
        "Schedule a team meeting tomorrow at 2pm for 1 hour"
    )
    print(response['output'])

asyncio.run(main())
```

### Direct Execution

You can also run the agent directly:

```bash
python3 -m admin_agent.agent
```

## Admin Agent Capabilities

The admin agent can:

- **List calendars**: View all available Google calendars
- **List events**: Show upcoming events with filters
- **Create events**: Add new calendar events with details
- **Update events**: Modify existing events
- **Delete events**: Remove events from calendar
- **Smart scheduling**: Help find available time slots

## MCP Tools

The agent uses these Google Calendar MCP tools:

- `list_calendars()` - List all available calendars
- `list_events()` - Get events from a calendar
- `create_event()` - Create a new event
- `update_event()` - Update an existing event
- `delete_event()` - Delete an event

## Authentication

On first use, the Google Calendar MCP server will:
1. Open a browser for OAuth authentication
2. Save your tokens securely
3. Automatically refresh tokens when needed

## LangSmith Monitoring

All agent interactions are automatically traced in LangSmith:
- View at: https://smith.langchain.com
- Project: `front-desk`

## Contributing

This is a personal project, but feel free to fork and adapt for your own use!
