# OpenAI Agents SDK Tutorial & Chatbot

This project is a comprehensive guide to understanding and utilizing the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/). It includes a step-by-step Quarto tutorial outlining key concepts and a capstone Streamlit project integrating all of those features into a functional chatbot.

## Environment Setup

Follow these steps to set up the development environment required to run both the tutorial and the final project:

1. **Clone or enter the directory:**
   Navigate into this project's directory in your terminal.

2. **Create a virtual environment:**
   We recommend using a Python virtual environment to manage dependencies locally.
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies:**
   Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

   *Note: This will install `openai-agents`, `quarto-cli`, `streamlit`, `mcp`, and other necessary libraries.*

5. **Configure Environment Variables:**
   Copy the example environment file and fill in your API key:
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and replace `your_openai_api_key_here` with your actual OpenAI API key.

## Rendering the Tutorial

This project uses [Quarto](https://quarto.org/) to generate the tutorial. With the virtual environment activated, you can preview or render the book:

To preview the tutorial in your browser:
```bash
quarto preview
```

To render the tutorial as static HTML (output in `_book`):
```bash
quarto render
```

## Running the Final Project

The final project is a Streamlit chatbot demonstrating Agents, Tools, Guardrails, Handoffs, Context Management, and MCP. To run it:

```bash
streamlit run chatbot/app.py
```

## Project Structure

- `_quarto.yml`: Configuration file for the Quarto book.
- `index.qmd` - `07-final-project.qmd`: Chapters covering each major concept.
- `chatbot/`: Directory containing the Streamlit application (`app.py`) and agent logic (`agents.py`).
- requirements.txt: Python dependencies.
