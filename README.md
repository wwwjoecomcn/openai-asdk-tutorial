# OpenAI Agents SDK Tutorial & Chatbot

This project is a comprehensive guide to understanding and utilizing the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/). It includes an interactive Jupyter Notebook RISE slide presentation outlining key concepts and a capstone Streamlit chatbot integrating all of those features.

## Environment Setup

Follow these steps to set up the development environment required to run both the tutorial and the final project.

> **Requirements:** Python 3.11+

### macOS / Linux

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Open .env and replace `your_openai_api_key_here` with your actual OpenAI API key
```

### Windows (PowerShell)

```powershell
# 1. Allow script execution (one-time, run as Administrator if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
copy .env.example .env
# Open .env and replace `your_openai_api_key_here` with your actual OpenAI API key
```

> **Windows note:** If you use Command Prompt instead of PowerShell, activate with `venv\Scripts\activate.bat`.

## Viewing the Interactive Presentation

This project uses Jupyter Notebook with the [RISE](https://rise.readthedocs.io/) extension to generate the interactive tutorial slides where you can execute Python code natively.

1. Start the Jupyter Notebook server:
   ```bash
   jupyter notebook slides.ipynb
   ```

2. Once the notebook opens in your browser, click the "Enter/Exit RISE Slideshow" button on the toolbar (or press `Alt-R`) to begin the presentation.

## Running the Final Project

The final project is a Streamlit chatbot demonstrating Agents, Tools, Guardrails, Handoffs, Context Management, and MCP integrations natively. To run it:

```bash
streamlit run chatbot/app.py
```

## Project Structure

- `slides.ipynb`: Interactive Jupyter Notebook presentation tutorial via RISE.
- `chatbot/`: Directory containing the Streamlit application (`app.py`), agent definitions (`bot_agents.py`), and a mock FastMCP server (`mock_mcp_server.py`).
- `requirements.txt`: Python dependencies.
