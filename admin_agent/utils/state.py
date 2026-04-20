"""Agent state definition for the admin agent."""
from typing import Annotated
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AdminAgentState(TypedDict):
    """State for the admin agent."""
    messages: Annotated[list, add_messages]
