import pytest
import lihil_mcp


def test_lazy_import_lihil_mcp():
    # This should trigger the lazy import
    LihilMCP = lihil_mcp.LihilMCP
    assert LihilMCP is not None
    assert LihilMCP.__name__ == "LihilMCP"


def test_lazy_import_lihil_mcp_transport():
    # This should trigger the lazy import
    LihilMCPTransport = lihil_mcp.LihilMCPTransport
    assert LihilMCPTransport is not None
    assert LihilMCPTransport.__name__ == "LihilMCPTransport"


def test_lazy_import_mcp_middleware():
    # This should trigger the lazy import
    MCPMiddleware = lihil_mcp.MCPMiddleware
    assert MCPMiddleware is not None
    assert MCPMiddleware.__name__ == "MCPMiddleware"


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