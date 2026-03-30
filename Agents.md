# Agent Workspace Context

## Project Overview
This repository contains a step-by-step tutorial and a capstone application demonstrating the official **OpenAI Agents Python SDK**. The project is split into two logical parts:
1. **Jupyter Notebook + RISE Documentation**: A tutorial formatted as a Jupyter Notebook (`slides.ipynb`) explaining key agent concepts, intended for presentation with RISE.
2. **Streamlit Chatbot**: A fully functional multi-agent UI application located in the `chatbot/` directory.

## Technology Stack
- **Python**: `3.11+`
- **Frameworks**: `openai-agents`, `streamlit`, `mcp` (Model Context Protocol).
- **Documentation**: [Jupyter Notebook + RISE](https://rise.readthedocs.io/)

## Environment Setup

### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your OPENAI_API_KEY
```

### Windows (PowerShell)
```powershell
# One-time: allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # then add your OPENAI_API_KEY
```
> If using Command Prompt: `venv\Scripts\activate.bat`

## Directory Structure
- `slides.ipynb`: A Jupyter Notebook interactive slide presentation detailing Agents, Tools, Context, Guardrails, Handoffs, and MCP concepts. This notebook is designed to be presented using the RISE extension.
- `chatbot/app.py`: The Streamlit frontend. It initializes memory (`st.session_state`), configures guardrails, spins up the MCP StdIO server natively, builds the agent schemas, and executes `Runner.run`.
- `chatbot/bot_agents.py`: Contains the raw python definitions for our Agents (`search_agent`, `triage_agent`) and python-native tools (e.g., `@function_tool async def search_weather(...)`).
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
- Do not alter the base `.ipynb` notebook without properly updating the RISE slide metadata tags, which manage the presentation boundaries. 
- Ensure any added API calls utilize the `openai` module properly with synchronous error handling specifically for HTTP 429 Quota Rate Limits.

## Important Commands

### macOS / Linux
- Run Streamlit: `streamlit run chatbot/app.py`
- Start Jupyter Presentation: `jupyter notebook slides.ipynb`

### Windows (PowerShell)
- Run Streamlit: `python -m streamlit run chatbot/app.py`
- Start Jupyter Presentation: `jupyter notebook slides.ipynb`
