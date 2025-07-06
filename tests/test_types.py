import pytest
from lihil_mcp.types import MCPError, MCPRegistrationError, MCPToolInfo, MCPResourceInfo


def test_mcp_error():
    error = MCPError("Test error")
    assert str(error) == "Test error"


def test_mcp_registration_error():
    error = MCPRegistrationError("Registration failed")
    assert str(error) == "Registration failed"


def test_mcp_tool_info():
    tool = MCPToolInfo(
        name="test_tool",
        description="A test tool",
        inputSchema={"type": "object"}
    )
    assert tool.name == "test_tool"
    assert tool.description == "A test tool"
    assert tool.inputSchema == {"type": "object"}


def test_mcp_resource_info():
    resource = MCPResourceInfo(
        uri="test://resource",
        name="Test Resource",
        description="A test resource",
        mimeType="application/json"
    )
    assert resource.uri == "test://resource"
    assert resource.name == "Test Resource"
    assert resource.description == "A test resource"
    assert resource.mimeType == "application/json"