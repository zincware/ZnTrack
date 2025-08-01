"""ZnTrack Model Context Provider (MCP) integration.

Example
-------
To connect the ZnTrack MCP server to claude code at the current working directory, run:

```bash
bunx @anthropic-ai/claude-code mcp add zntrack-server -- uv run --project "$(pwd)" zntrack-mcp
bunx @anthropic-ai/claude-code
```
"""

from zntrack.mcp.server import mcp

__all__ = ["mcp"]
