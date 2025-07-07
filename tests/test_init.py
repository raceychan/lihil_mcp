import pytest
import lihil_mcp


def test_import_lihil_mcp():
    LihilMCP = lihil_mcp.LihilMCP
    assert LihilMCP is not None
    assert LihilMCP.__name__ == "LihilMCP"




def test_invalid_attribute_raises_error():
    with pytest.raises(AttributeError, match="module 'lihil_mcp' has no attribute 'NonExistentClass'"):
        _ = lihil_mcp.NonExistentClass


def test_direct_imports_available():
    # Test that direct imports work
    from lihil_mcp import MCPConfig, mcp_tool, mcp_resource, get_mcp_metadata
    assert MCPConfig is not None
    assert mcp_tool is not None
    assert mcp_resource is not None
    assert get_mcp_metadata is not None