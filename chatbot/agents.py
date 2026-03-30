import os
import sys
from agents import Agent, function_tool

# ================= TOOLS =================

@function_tool
async def search_weather(location: str) -> str:
    """Gets the weather for a given location."""
    return f"The weather in {location} is rainy and 65°F."

# ================= AGENTS =================

# 1. MCP Support Agent
# Note: In a real environment, you'd dynamically connect to MCP. 
# Here we define an agent that *assumes* it will be injected with MCP tools dynamically.
support_agent = Agent(
    name="SupportAgent",
    instructions="You provide technical support. If asked for logs, use your fetch_internal_logs tool.",
    model="gpt-4o"
)

search_agent = Agent(
    name="SearchAgent",
    instructions="You are a weather searching bot.",
    tools=[search_weather],
    model="gpt-4o"
)

# 3. Triage Agent
triage_agent = Agent(
    name="TriageAgent",
    instructions=(
        "You are the main Router agent. "
        "Greet the user. If they want to check the weather, hand off to SearchAgent. "
        "If they need technical support or system logs, hand off to SupportAgent."
    ),
    handoffs=[search_agent, support_agent],
    model="gpt-4o"
)

# ================= MCP HELPER =================

# MCP setup is handled inside app.py by injecting the MCPServerStdio natively into the agent.
