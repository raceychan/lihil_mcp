import pytest
from lihil_mcp.decorators import mcp_tool, mcp_resource, get_mcp_metadata, is_mcp_endpoint


def test_mcp_tool_decorator():
    @mcp_tool(description="Test tool")
    def test_function():
        return "test"
    
    metadata = get_mcp_metadata(test_function)
    assert metadata is not None
    assert metadata.type == "tool"
    assert metadata.description == "Test tool"


def test_mcp_resource_decorator():
    @mcp_resource(uri_template="test://resource", title="Test Resource")
    def test_resource():
        return {"data": "test"}
    
    metadata = get_mcp_metadata(test_resource)
    assert metadata is not None
    assert metadata.type == "resource"
    assert metadata.uri_template == "test://resource"
    assert metadata.title == "Test Resource"


def test_get_mcp_metadata_no_metadata():
    def regular_function():
        pass
    
    metadata = get_mcp_metadata(regular_function)
    assert metadata is None


def test_is_mcp_endpoint():
    @mcp_tool(description="Test tool")
    def mcp_function():
        return "test"
    
    def regular_function():
        pass
    
    assert is_mcp_endpoint(mcp_function) is True
    assert is_mcp_endpoint(regular_function) is False