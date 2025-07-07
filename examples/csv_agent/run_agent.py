#!/usr/bin/env python3
"""
Simple script to run the CSV AI Agent with proper MCP integration.
"""

import sys
import os

# Add the parent directory to path so we can import lihil_mcp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from csv_agent import create_csv_agent_app
from lihil_mcp import LihilMCP

def main():
    """Run the CSV AI Agent with MCP integration."""
    
    # Create the app and config
    app, mcp_config = create_csv_agent_app()
    
    # Create LihilMCP instance
    lihil_mcp = LihilMCP(app, mcp_config)
    
    # Setup MCP tools and resources for display
    lihil_mcp.setup_mcp_tools_and_resources()
    
    # Get the integrated ASGI app with MCP support
    integrated_app = lihil_mcp.get_asgi_app()
    
    print("Starting CSV AI Agent with MCP integration...")
    print(f"Server: {mcp_config.server_name}")
    print(f"MCP enabled: {mcp_config.enabled}")
    print(f"Auto-expose: {mcp_config.auto_expose}")
    print()
    print("Available MCP Tools:")
    for tool_name in lihil_mcp.tools:
        print(f"  - {tool_name}")
    print()
    print("Available MCP Resources:")
    for resource_uri in lihil_mcp.resources:
        print(f"  - {resource_uri}")
    print()
    print("Server starting on http://localhost:8000")
    print("Press Ctrl+C to stop")
    
    # Start the server
    import uvicorn
    uvicorn.run(integrated_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()