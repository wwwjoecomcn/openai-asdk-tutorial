import asyncio
import os
import sys
from dotenv import load_dotenv

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

# Local imports from the same directory structure
from .agents import triage_agent, search_agent, search_weather

load_dotenv()

async def main():
    script_path = os.path.join(os.path.dirname(__file__), "mock_mcp_server.py")
    
    # Run the MCP Server natively
    async with MCPServerStdio(
        params={
            "command": sys.executable,
            "args": [script_path]
        }
    ) as server:
        
        # We need to construct the SupportAgent here to attach it to the MCP server
        session_support_agent = Agent(
            name="SupportAgent",
            instructions="You provide technical support. If asked for logs, use your fetch_internal_logs tool.",
            mcp_servers=[server],
            model="gpt-4o"
        )
        
        # TriageAgent handles the dynamic routing
        session_triage_agent = Agent(
            name="TriageAgent",
            instructions=(
                "You are the main Router agent. Greet the user. "
                "If they want to check the weather, hand off to SearchAgent. "
                "If they need technical support or system logs, hand off to SupportAgent."
            ),
            handoffs=[search_agent, session_support_agent],
            model="gpt-4o"
        )

        history = []
        print("🤖 Multi-Agent CLI started! Type 'exit' to quit.\n")
        
        while True:
            try:
                user_input = input("\033[94mYou:\033[0m ")
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                    
                # Guardrails Pre-check
                if "admin" in user_input.lower():
                    print("\033[92mAssistant:\033[0m Guardrail Triggered: You cannot query admin resources.")
                    continue
                    
                history.append({"role": "user", "content": user_input})
                
                # Execute run across agents
                print("\033[90mThinking...\033[0m", end="\r")
                result = await Runner.run(session_triage_agent, input=history)
                output = result.final_output
                
                # Guardrails Post-check
                if "secret password" in output.lower():
                    output = "[REDACTED BY GUARDRAILS]"
                
                print(f"\033[92mAssistant:\033[0m {output}\n")
                history.append({"role": "assistant", "content": output})
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\n\033[91mError: {e}\033[0m\n")

if __name__ == "__main__":
    asyncio.run(main())
