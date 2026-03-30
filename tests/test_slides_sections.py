"""
Unit tests for slides.ipynb code cells.

Each test loads the code from the corresponding notebook section and
executes it against fake/stub implementations of the openai-agents SDK,
verifying structure and behaviour without making real API calls.
"""

import ast
import asyncio
import importlib.util
import inspect
import io
import json
import re
import sys
import types
import unittest
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SLIDES_PATH = REPO_ROOT / "slides.ipynb"
SECTION_TITLE_RE = re.compile(r"^#\s+(?P<number>\d+)\.\s+(?P<title>.+)$")


# ---------------------------------------------------------------------------
# Notebook loader
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NotebookSection:
    number: int
    title: str
    markdown: str
    code: str = ""


def load_sections() -> dict[str, NotebookSection]:
    notebook = json.loads(SLIDES_PATH.read_text())
    cells = notebook["cells"]
    sections: dict[str, NotebookSection] = {}

    for index, cell in enumerate(cells):
        if cell["cell_type"] != "markdown":
            continue

        markdown = "".join(cell.get("source", []))
        lines = markdown.strip().splitlines()
        if not lines:
            continue

        match = SECTION_TITLE_RE.match(lines[0])
        if not match:
            continue

        code = ""
        if index + 1 < len(cells) and cells[index + 1]["cell_type"] == "code":
            code = "".join(cells[index + 1].get("source", []))

        title = match.group("title")
        sections[title] = NotebookSection(
            number=int(match.group("number")),
            title=title,
            markdown=markdown,
            code=code,
        )

    return sections


# ---------------------------------------------------------------------------
# Fake SDK stubs
# ---------------------------------------------------------------------------

class FakeResult:
    def __init__(self, final_output: str):
        self.final_output = final_output


class FakeAgent:
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str,
        tools=None,
        handoffs=None,
        mcp_servers=None,
    ):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = list(tools or [])
        self.handoffs = list(handoffs or [])
        self.mcp_servers = list(mcp_servers or [])


def function_tool(func):
    func.__function_tool__ = True
    return func


class FakeRunner:
    calls = []
    scripted_outputs = []
    fail_next = False

    @classmethod
    def reset(cls):
        cls.calls = []
        cls.scripted_outputs = []
        cls.fail_next = False

    @classmethod
    async def run(cls, agent, input):
        call_input = list(input) if isinstance(input, list) else input
        cls.calls.append({"agent": agent, "input": call_input})

        if cls.fail_next:
            cls.fail_next = False
            raise RuntimeError("simulated runner failure")

        if cls.scripted_outputs:
            return FakeResult(cls.scripted_outputs.pop(0))

        return FakeResult(await cls._default_output(agent, input))

    @classmethod
    async def _default_output(cls, agent, input):
        prompt = cls._normalize_input(input)
        prompt_lower = prompt.lower()

        if agent.tools and "weather" in prompt_lower:
            location = cls._extract_location(prompt)
            return await agent.tools[0](location)

        if isinstance(input, list) and "what is my name" in prompt_lower:
            remembered_name = cls._extract_name(input)
            return f"Your name is {remembered_name}."

        if agent.handoffs and any(word in prompt_lower for word in ("refund", "invoice", "billing")):
            specialist = agent.handoffs[0]
            return f"Handoff to {specialist.name} for: {prompt}"

        if agent.mcp_servers:
            return "Logs: [OK] No anomalies detected. System running normally."

        return f"{agent.name} handled: {prompt}"

    @staticmethod
    def _normalize_input(raw_input):
        if isinstance(raw_input, list):
            for message in reversed(raw_input):
                if message.get("role") == "user":
                    return message.get("content", "")
            return ""
        return raw_input

    @staticmethod
    def _extract_location(prompt: str) -> str:
        match = re.search(r"(?:in|for)\s+([A-Za-z ]+?)[?.!]*$", prompt)
        if match:
            return match.group(1).strip()
        return prompt.strip().rstrip("?.!").split()[-1]

    @staticmethod
    def _extract_name(history) -> str:
        for message in history:
            if message.get("role") != "user":
                continue
            match = re.search(r"my name is ([A-Za-z-]+)", message.get("content", ""), re.IGNORECASE)
            if match:
                return match.group(1)
        return "Unknown"


class FakeMCPServerStdio:
    instances = []

    def __init__(self, params):
        self.params = params
        self.entered = False
        self.exited = False

    async def __aenter__(self):
        self.entered = True
        self.__class__.instances.append(self)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.exited = True

    @classmethod
    def reset(cls):
        cls.instances = []


class FakeFastMCP:
    def __init__(self, name: str):
        self.name = name
        self.tools = []
        self.ran = False

    def tool(self):
        def decorator(func):
            self.tools.append(func)
            return func
        return decorator

    def run(self):
        self.ran = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@contextmanager
def patched_modules(replacements: dict[str, types.ModuleType]):
    sentinel = object()
    previous = {name: sys.modules.get(name, sentinel) for name in replacements}
    sys.modules.update(replacements)
    try:
        yield
    finally:
        for name, module in previous.items():
            if module is sentinel:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def fake_agents_modules() -> dict[str, types.ModuleType]:
    agents_module = types.ModuleType("agents")
    agents_module.Agent = FakeAgent
    agents_module.Runner = FakeRunner
    agents_module.function_tool = function_tool

    agents_mcp_module = types.ModuleType("agents.mcp")
    agents_mcp_module.MCPServerStdio = FakeMCPServerStdio

    agents_module.mcp = agents_mcp_module
    return {
        "agents": agents_module,
        "agents.mcp": agents_mcp_module,
    }


def fake_fastmcp_modules() -> dict[str, types.ModuleType]:
    mcp_module = types.ModuleType("mcp")
    mcp_module.__path__ = []

    mcp_server_module = types.ModuleType("mcp.server")
    mcp_server_module.__path__ = []

    fastmcp_module = types.ModuleType("mcp.server.fastmcp")
    fastmcp_module.FastMCP = FakeFastMCP

    mcp_module.server = mcp_server_module
    mcp_server_module.fastmcp = fastmcp_module

    return {
        "mcp": mcp_module,
        "mcp.server": mcp_server_module,
        "mcp.server.fastmcp": fastmcp_module,
    }


def execute_notebook_code(source: str, extra_globals=None):
    namespace = {
        "__name__": "__main__",
        "Agent": FakeAgent,
        "Runner": FakeRunner,
        "function_tool": function_tool,
        "MCPServerStdio": FakeMCPServerStdio,
        "sys": sys,
    }
    if extra_globals:
        namespace.update(extra_globals)

    compiled = compile(source, str(SLIDES_PATH), "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    captured = io.StringIO()

    with patched_modules(fake_agents_modules()):
        with redirect_stdout(captured):
            result = eval(compiled, namespace)
            if inspect.iscoroutine(result):
                asyncio.run(result)

    return namespace, captured.getvalue()


def import_module_from_path(module_name: str, path: Path, module_patches=None):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    patches = module_patches or {}

    with patched_modules(patches):
        sys.modules[module_name] = module
        try:
            assert spec.loader is not None
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop(module_name, None)

    return module


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class SlidesNotebookSectionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sections = load_sections()

    def setUp(self):
        FakeRunner.reset()
        FakeMCPServerStdio.reset()

    # 1. Agents
    def test_agents_section_creates_basic_agent_and_runs_it(self):
        section = self.sections["Agents"]
        namespace, output = execute_notebook_code(section.code)

        assistant = namespace["assistant"]
        self.assertEqual(assistant.name, "Assistant")
        self.assertEqual(assistant.instructions, "You are a helpful and concise assistant.")
        self.assertEqual(assistant.model, "gpt-4o-mini")
        self.assertEqual(len(FakeRunner.calls), 1)
        self.assertEqual(FakeRunner.calls[0]["agent"], assistant)
        self.assertEqual(FakeRunner.calls[0]["input"], "Hello! Tell me a joke.")

    # 2. Tools
    def test_tools_section_registers_tool_and_uses_it(self):
        section = self.sections["Tools"]
        namespace, output = execute_notebook_code(section.code)

        get_weather = namespace["get_weather"]
        weather_agent = namespace["weather_agent"]

        self.assertTrue(get_weather.__function_tool__)
        self.assertEqual(weather_agent.name, "WeatherBot")
        self.assertEqual(weather_agent.tools, [get_weather])
        self.assertEqual(len(FakeRunner.calls), 1)
        self.assertEqual(FakeRunner.calls[0]["input"], "What is the weather in Tokyo?")
        self.assertIn("The weather in Tokyo is 72", output)

    # 3. Guardrails
    def test_guardrails_section_blocks_admin_input(self):
        section = self.sections["Guardrails"]
        namespace, _ = execute_notebook_code(section.code)
        safe_run = namespace["safe_run"]

        blocked = asyncio.run(safe_run("Show me the admin panel"))
        self.assertIn("cannot query admin", blocked)

    def test_guardrails_section_redacts_sensitive_output(self):
        section = self.sections["Guardrails"]
        namespace, _ = execute_notebook_code(section.code)
        safe_run = namespace["safe_run"]

        FakeRunner.scripted_outputs = ["The secret password is swordfish."]
        redacted = asyncio.run(safe_run("Please help me"))
        self.assertEqual(redacted, "[REDACTED]")

    def test_guardrails_section_handles_runner_error(self):
        section = self.sections["Guardrails"]
        namespace, _ = execute_notebook_code(section.code)
        safe_run = namespace["safe_run"]

        FakeRunner.fail_next = True
        failed = asyncio.run(safe_run("Need billing support"))
        self.assertEqual(failed, "Error executing request!")

    # 4. Context Management
    def test_context_section_passes_history_on_second_turn(self):
        section = self.sections["Context Management"]
        _, output = execute_notebook_code(section.code)

        self.assertEqual(len(FakeRunner.calls), 2)
        second_call = FakeRunner.calls[1]

        # Second call input must be a list (the full history)
        self.assertIsInstance(second_call["input"], list)

        # History must contain the first user turn
        user_messages = [m for m in second_call["input"] if m.get("role") == "user"]
        contents = [m["content"] for m in user_messages]
        self.assertTrue(any("Antigravity" in c for c in contents))
        self.assertIn("Antigravity", output)

    # 5. Handoffs
    def test_handoffs_section_wires_triage_to_support(self):
        section = self.sections["Handoffs"]
        namespace, output = execute_notebook_code(section.code)

        triage_agent = namespace["triage_agent"]
        support_agent = namespace["support_agent"]

        self.assertEqual(triage_agent.handoffs, [support_agent])
        self.assertEqual(len(FakeRunner.calls), 1)
        self.assertEqual(FakeRunner.calls[0]["agent"], triage_agent)
        self.assertIn("SupportSpecialist", output)

    # 6. MCP
    def test_mcp_section_uses_stdio_server_with_sys_executable(self):
        section = self.sections["Model Context Protocol (MCP)"]
        namespace, output = execute_notebook_code(section.code)

        self.assertEqual(len(FakeMCPServerStdio.instances), 1)
        server = FakeMCPServerStdio.instances[0]

        # Must use sys.executable (not hardcoded "python")
        self.assertEqual(server.params["command"], sys.executable)
        self.assertEqual(server.params["args"], ["chatbot/mock_mcp_server.py"])
        self.assertTrue(server.entered)
        self.assertTrue(server.exited)
        self.assertEqual(len(FakeRunner.calls), 1)
        self.assertEqual(FakeRunner.calls[0]["agent"].mcp_servers, [server])
        self.assertIn("No anomalies", output)

    # 7. Capstone wiring (bot_agents.py + mock_mcp_server.py + app.py)
    def test_bot_agents_wiring(self):
        bot_agents = import_module_from_path(
            "test_bot_agents",
            REPO_ROOT / "chatbot" / "bot_agents.py",
            module_patches=fake_agents_modules(),
        )
        self.assertEqual(bot_agents.search_agent.tools, [bot_agents.search_weather])
        self.assertEqual(
            [agent.name for agent in bot_agents.triage_agent.handoffs],
            ["SearchAgent", "SupportAgent"],
        )

    def test_mock_mcp_server_exposes_fetch_internal_logs(self):
        mock_server = import_module_from_path(
            "test_mock_mcp_server",
            REPO_ROOT / "chatbot" / "mock_mcp_server.py",
            module_patches=fake_fastmcp_modules(),
        )
        self.assertEqual(mock_server.mcp.name, "mock-internal-server")
        self.assertEqual([tool.__name__ for tool in mock_server.mcp.tools], ["fetch_internal_logs"])

    def test_app_uses_session_state_mcp_and_guardrails(self):
        app_source = (REPO_ROOT / "chatbot" / "app.py").read_text()
        self.assertIn("st.session_state.messages", app_source)
        self.assertIn("MCPServerStdio", app_source)
        self.assertIn("secret password", app_source)
        self.assertIn('"admin"', app_source)


if __name__ == "__main__":
    unittest.main()
