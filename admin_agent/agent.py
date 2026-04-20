"""Admin Agent - Your Personal Assistant with Google Calendar Integration.

This agent uses LangChain with OpenRouter and Google Calendar MCP tools.
LangSmith tracing is automatically enabled via environment variables.
"""

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from admin_agent.utils.prompt import ADMIN_AGENT_SYSTEM_PROMPT
from collections.abc import Callable
from langchain.agents.middleware import ModelRequest, ModelResponse, AgentMiddleware, HumanInTheLoopMiddleware
from langchain.messages import SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from common_tools.gcalendar.tools import CALENDAR_TOOLS, CALENDAR_TOOLS_D
from common_tools.gmail.tools import GMAIL_TOOLS, GMAIL_TOOLS_D
from common_tools.filesystem.tools import FILE_SYSTEM_TOOLS, FILE_SYSTEM_TOOLS_D

ALL_TOOLS = CALENDAR_TOOLS + GMAIL_TOOLS + FILE_SYSTEM_TOOLS
UNSAFE_TOOLS = CALENDAR_TOOLS_D + GMAIL_TOOLS_D + FILE_SYSTEM_TOOLS_D

load_dotenv()

class AdminAgent:
    """Personal assistant agent with Google Calendar integration."""

    def __init__(self):
        """Initialize the admin agent with OpenRouter and calendar tools."""

        # Initialize the model via OpenRouter
        # self.model = ChatOpenAI(
        #     model="anthropic/claude-3.7-sonnet",
        #     openai_api_base="https://openrouter.ai/api/v1",
        #     openai_api_key=os.getenv("OPEN_ROUTER_API_KEY"),
        #     temperature=0.7,
        # )
        
        # Get base URL and ensure it has /v1 suffix for OpenAI compatibility
        base_url = os.getenv('LM_STUDIO_BASE_URL', 'http://127.0.0.1:1234')
        if not base_url.endswith('/v1'):
            base_url = f"{base_url}/v1"
        
        self.model = ChatOpenAI(
            model=os.getenv('LM_STUDIO_MODEL'),
            openai_api_base=base_url,
            openai_api_key="not-needed"  # LM Studio doesn't require key but client validates it
        )

        # Date context middleware - adds current date/time to help with relative dates
        class DateContextMiddleware(AgentMiddleware):
            """Middleware that injects current date/time context into system prompts."""
            
            def _create_date_context(self) -> str:
                """Generate the date context string."""
                now = datetime.now()
                day_name = now.strftime("%A")
                date_str = now.strftime("%B %d, %Y")
                time_str = now.strftime("%I:%M %p")
                timezone_str = now.strftime("%Z") or "Eastern Time"
                
                return (
                    f"\n\n=== CURRENT DATE/TIME CONTEXT ===\n"
                    f"Current Date: {day_name}, {date_str}\n"
                    f"Current Time: {time_str} ({timezone_str})\n"
                    f"ISO Format: {now.isoformat()}\n"
                    f"\nIMPORTANT: When users refer to relative dates like 'this weekend', "
                    f"'next Friday', 'this Monday', 'April 9-12', etc., calculate the actual "
                    f"dates based on the current date above. Always use YEAR {now.year} unless "
                    f"the user explicitly specifies a different year.\n"
                    f"================================="
                )
            
            def wrap_model_call(
                self,
                request: ModelRequest,
                handler: Callable[[ModelRequest], ModelResponse],
            ) -> ModelResponse:
                """Sync version: Add date context to system message."""
                date_context = self._create_date_context()
                new_content = list(request.system_message.content_blocks) + [
                    {"type": "text", "text": date_context}
                ]
                new_system_message = SystemMessage(content=new_content)
                return handler(request.override(system_message=new_system_message))
            
            async def awrap_model_call(
                self,
                request: ModelRequest,
                handler: Callable[[ModelRequest], ModelResponse],
            ) -> ModelResponse:
                """Async version: Add date context to system message."""
                date_context = self._create_date_context()
                new_content = list(request.system_message.content_blocks) + [
                    {"type": "text", "text": date_context}
                ]
                new_system_message = SystemMessage(content=new_content)
                return await handler(request.override(system_message=new_system_message))
            
        # Human In the Loop Middleware
        human_in_the_loop = HumanInTheLoopMiddleware(
            interrupt_on={unsafe_tool.func.__name__: True for unsafe_tool in UNSAFE_TOOLS}
        )

        # Create the agent with calendar tools and date context middleware
        self.agent = create_agent(
            model=self.model, 
            tools=ALL_TOOLS, 
            system_prompt=ADMIN_AGENT_SYSTEM_PROMPT,
            middleware=[DateContextMiddleware(), human_in_the_loop],
            checkpointer=InMemorySaver()
        )


def get_agent():
    graph = AdminAgent()
    return graph.agent


async def main():
    """Example usage of the admin agent."""
    print("🤖 Admin Agent initialized!\n")
    print("=" * 60)
    print("This is your personal assistant with Google Calendar access.")
    print("LangSmith tracing is enabled for this session.")
    print("=" * 60)
    print()

    # Create the agent
    agent = AdminAgent()

    # Example interaction
    print("User: What events do I have coming up?")
    print()

    response = await agent.ainvoke(
        "What events do I have coming up in the next 7 days?"
    )

    print()
    print("=" * 60)
    print(f"Agent: {response['output']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
