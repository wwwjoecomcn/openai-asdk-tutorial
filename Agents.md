# Agent Workspace Context

## Project Overview
This repository contains a step-by-step tutorial and a capstone application demonstrating the official **OpenAI Agents Python SDK**. The project is split into two logical parts:
1. **Quarto Documentation**: A tutorial formatted as a Quarto book (`*.qmd` files) explaining key agent concepts.
2. **Streamlit Chatbot**: A fully functional multi-agent UI application located in the `chatbot/` directory.

## Technology Stack
- **Python**: `3.11+`
- **Frameworks**: `openai-agents`, `streamlit`, `mcp` (Model Context Protocol).
- **Documentation**: [Quarto](https://quarto.org)

## Directory Structure
- `*.qmd` & `_quarto.yml`: Quarto configuration and markdown tutorial chapters detailing Agents, Tools, Context, Guardrails, Handoffs, and MCP.
- `chatbot/app.py`: The Streamlit frontend. It initializes memory (`st.session_state`), configures guardrails, spins up the MCP StdIO server natively, builds the agent schemas, and executes `Runner.run`.
- `chatbot/agents.py`: Contains the raw python definitions for our Agents (`search_agent`, `triage_agent`) and python-native tools (e.g., `@function_tool async def search_weather(...)`).
- `chatbot/mock_mcp_server.py`: An autonomous local `FastMCP` server demonstrating how external resources can be mapped to an agent using the Model Context Protocol. Exposed over `MCPServerStdio`.
- `venv/`: Standard Python virtual environment.
- `.env`: Contains the `OPENAI_API_KEY`. (Template provided in `.env.example`).

## Architecture & Agent Topology
The capstone utilizes a **Routing/Triage Pattern**:
1. **TriageAgent**: The main entry point. Greets users and determines user intent.
2. If weather/search related -> hands off to **SearchAgent** (equipped with standard Python tools).
3. If logs/technical support related -> hands off to **SupportAgent** (equipped seamlessly with tools from the external MCP server).

## Guidelines for AI Assistants working in this repo
- **Do NOT** manually manage JSON schemas for standard Python functions; always use the `@function_tool` decorator dynamically imported from `agents` (the OpenAI Agents object).
- When modifying the `SupportAgent` or the `MCP` integration, note that `SupportAgent` evaluates dynamically inside `app.py` directly alongside the `async with MCPServerStdio(...) as server` block to tie the server lifecycle to the Streamlit execution sequence.
- Do not alter the base `.qmd` Quarto structure without explicitly regenerating the output using `quarto render`. 
- Ensure any added API calls utilize the `openai` module properly with synchronous error handling specifically for HTTP 429 Quota Rate Limits.

## Important Commands
- Run Streamlit: `streamlit run chatbot/app.py`
- Run Quarto preview: `quarto preview`
- Run Quarto render: `quarto render`
