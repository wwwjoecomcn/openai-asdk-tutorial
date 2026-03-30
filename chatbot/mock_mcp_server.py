from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mock-internal-server")

@mcp.tool()
async def fetch_internal_logs(resource: str) -> str:
    """Fetches internal mock logs. Useful for troubleshooting."""
    return f"Logs for {resource}: [OK] No anomalies detected. System running normally."

if __name__ == "__main__":
    mcp.run()
