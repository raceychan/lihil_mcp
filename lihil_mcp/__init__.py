"""
MCP (Model Context Protocol) plugin for lihil framework.

This plugin enables lihil applications to expose their endpoints as MCP tools and resources,
allowing them to be used by MCP-compatible clients like Claude Code.

This plugin provides proper dependency inversion - MCP depends on Lihil, not the other way around.
To use MCP functionality, create a LihilMCP instance and configure it with your lihil app.
"""

from .config import MCPConfig
from .decorators import get_mcp_metadata, mcp_resource, mcp_tool
from .server import LihilMCP

__all__ = [
    "MCPConfig",
    "LihilMCP",
    "mcp_tool",
    "mcp_resource",
    "get_mcp_metadata",
]
