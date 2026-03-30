import os
import sys
import streamlit as st
import asyncio
from dotenv import load_dotenv

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

# Local imports
from bot_agents import triage_agent, search_agent, search_weather

load_dotenv()

st.set_page_config(page_title="OpenAI Agents SDK Chatbot", page_icon="🤖")

st.title("OpenAI Agents SDK + MCP Capstone")
st.markdown("A demonstration of Agents, Tools, Guardrails, Handoffs, Context, and MCP.")

# Initialize the history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to run the agent pipeline
async def run_agent_pipeline(user_input: str):
    # GUARDRAIL pre-check
    if "admin" in user_input.lower():
         yield "Guardrail Triggered: You cannot query admin resources."
         return

    # Assuming the app runs from the root or inside chatbot dir
    script_path = os.path.join(os.path.dirname(__file__), "mock_mcp_server.py")
    
    # Run the MCP Server natively as supported by SDK
    async with MCPServerStdio(
        params={
            "command": sys.executable,
            "args": [script_path]
        }
    ) as server:
        # Re-attach mcp_servers to the support_agent dynamically inside this scope
        # Wait, instead of mutating instantiated agents which might be immutable or shared state,
        # we can just reconstruct them here safely for the active session
        session_support_agent = Agent(
            name="SupportAgent",
            instructions="You provide technical support. If asked for logs, use your fetch_internal_logs tool.",
            mcp_servers=[server],
            model="gpt-4o"
        )
        
        session_triage_agent = Agent(
            name="TriageAgent",
            instructions=(
                "You are the main Router agent. "
                "Greet the user. If they want to check the weather, hand off to SearchAgent. "
                "If they need technical support or system logs, hand off to SupportAgent."
            ),
            handoffs=[search_agent, session_support_agent],
            model="gpt-4o"
        )
        
        # history will be a list of Message dicts
        history = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]
        
        # We pass the full history (which already includes the user's latest prompt) to input
        result = await Runner.run(
            session_triage_agent,
            input=history
        )
        
        output = result.final_output
        
        # GUARDRAIL post-check
        if "secret password" in output.lower():
            yield "[REDACTED BY GUARDRAILS]"
        else:
            yield output

# Render history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("How can I help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        # Since streamlit isn't fully async, we use asyncio.run
        async def generate_response():
            # Get generator (or just single string in this case)
            async for chunk in run_agent_pipeline(prompt):
                 response_placeholder.markdown(chunk)
                 st.session_state.messages.append({"role": "assistant", "content": chunk})
                 
        asyncio.run(generate_response())

