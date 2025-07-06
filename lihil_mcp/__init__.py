"""
MCP (Model Context Protocol) plugin for lihil framework.

This plugin enables lihil applications to expose their endpoints as MCP tools and resources,
allowing them to be used by MCP-compatible clients like Claude Code.

This plugin provides proper dependency inversion - MCP depends on Lihil, not the other way around.
To use MCP functionality, create a LihilMCP instance and configure it with your lihil app.
"""

# Import config and decorators which don't require mcp package
from .config import MCPConfig
from .decorators import mcp_tool, mcp_resource, get_mcp_metadata

# Lazy imports for components that require mcp package
def __getattr__(name):
    if name == "LihilMCP":
        from .server import LihilMCP
        return LihilMCP
    elif name == "LihilMCPTransport":
        from .transport import LihilMCPTransport
        return LihilMCPTransport
    elif name == "MCPMiddleware":
        from .transport import MCPMiddleware
        return MCPMiddleware
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ["MCPConfig", "LihilMCP", "mcp_tool", "mcp_resource", "get_mcp_metadata", "LihilMCPTransport", "MCPMiddleware"]
