import pytest
from unittest.mock import Mock, AsyncMock, patch

from lihil_mcp.transport import LihilMCPTransport, MCPMiddleware


class MockLihilMCP:
    def __init__(self, config):
        self.config = config
        self.mcp_server = Mock()
        self.app = AsyncMock()


class MockConfig:
    def __init__(self, mcp_path_prefix="/mcp"):
        self.mcp_path_prefix = mcp_path_prefix


@pytest.fixture
def mock_config():
    return MockConfig()


@pytest.fixture
def mock_lihil_mcp(mock_config):
    return MockLihilMCP(mock_config)


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_lihil_mcp_transport_init(mock_asgi_transport, mock_lihil_mcp):
    mock_transport_instance = Mock()
    mock_asgi_transport.return_value = mock_transport_instance
    
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    assert transport.mcp_server == mock_lihil_mcp
    assert transport.transport == mock_transport_instance
    assert transport.mcp_path_prefix == "/mcp"
    mock_asgi_transport.assert_called_once_with(mock_lihil_mcp.mcp_server)


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_lihil_mcp_transport_init_custom_prefix(mock_asgi_transport):
    mock_config = MockConfig("/custom-prefix")
    mock_lihil_mcp = MockLihilMCP(mock_config)
    mock_transport_instance = Mock()
    mock_asgi_transport.return_value = mock_transport_instance
    
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    assert transport.mcp_path_prefix == "/custom-prefix"


@patch('lihil_mcp.transport.ASGIServerTransport')
@pytest.mark.asyncio
async def test_transport_call_mcp_request(mock_asgi_transport, mock_lihil_mcp):
    mock_transport_instance = AsyncMock()
    mock_asgi_transport.return_value = mock_transport_instance
    
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {"type": "http", "path": "/mcp/test"}
    receive = AsyncMock()
    send = AsyncMock()
    
    await transport(scope, receive, send)
    
    mock_transport_instance.assert_called_once_with(scope, receive, send)
    mock_lihil_mcp.app.assert_not_called()


@patch('lihil_mcp.transport.ASGIServerTransport')
@pytest.mark.asyncio
async def test_transport_call_regular_request(mock_asgi_transport, mock_lihil_mcp):
    mock_transport_instance = AsyncMock()
    mock_asgi_transport.return_value = mock_transport_instance
    
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {"type": "http", "path": "/api/test"}
    receive = AsyncMock()
    send = AsyncMock()
    
    await transport(scope, receive, send)
    
    mock_transport_instance.assert_not_called()
    mock_lihil_mcp.app.assert_called_once_with(scope, receive, send)


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_non_http(mock_asgi_transport, mock_lihil_mcp):
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {"type": "websocket", "path": "/mcp/test"}
    
    assert transport._is_mcp_request(scope) is False


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_mcp_path_prefix(mock_asgi_transport, mock_lihil_mcp):
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {"type": "http", "path": "/mcp/test"}
    
    assert transport._is_mcp_request(scope) is True


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_custom_path_prefix(mock_asgi_transport):
    mock_config = MockConfig("/custom-mcp")
    mock_lihil_mcp = MockLihilMCP(mock_config)
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {"type": "http", "path": "/custom-mcp/test"}
    
    assert transport._is_mcp_request(scope) is True


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_json_rpc_header(mock_asgi_transport, mock_lihil_mcp):
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {
        "type": "http", 
        "path": "/api/test",
        "headers": [
            (b"content-type", b"application/json"),
            (b"custom-header", b"jsonrpc")
        ]
    }
    
    assert transport._is_mcp_request(scope) is True


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_jsonrpc_in_content_type(mock_asgi_transport, mock_lihil_mcp):
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {
        "type": "http", 
        "path": "/api/test",
        "headers": [
            (b"content-type", b"application/json; charset=utf-8; jsonrpc=2.0")
        ]
    }
    
    assert transport._is_mcp_request(scope) is True


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_json_content_type_no_jsonrpc(mock_asgi_transport, mock_lihil_mcp):
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {
        "type": "http", 
        "path": "/api/test",
        "headers": [
            (b"content-type", b"application/json")
        ]
    }
    
    assert transport._is_mcp_request(scope) is False


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_no_mcp_indicators(mock_asgi_transport, mock_lihil_mcp):
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {
        "type": "http", 
        "path": "/api/test",
        "headers": [
            (b"content-type", b"text/html")
        ]
    }
    
    assert transport._is_mcp_request(scope) is False


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_no_headers(mock_asgi_transport, mock_lihil_mcp):
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {"type": "http", "path": "/api/test"}
    
    assert transport._is_mcp_request(scope) is False


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_empty_headers(mock_asgi_transport, mock_lihil_mcp):
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {"type": "http", "path": "/api/test", "headers": []}
    
    assert transport._is_mcp_request(scope) is False


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_no_path(mock_asgi_transport, mock_lihil_mcp):
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {"type": "http"}
    
    assert transport._is_mcp_request(scope) is False


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_empty_path(mock_asgi_transport, mock_lihil_mcp):
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {"type": "http", "path": ""}
    
    assert transport._is_mcp_request(scope) is False


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_partial_path_match(mock_asgi_transport, mock_lihil_mcp):
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    # Path contains mcp but doesn't start with the prefix
    scope = {"type": "http", "path": "/api/mcp/test"}
    
    assert transport._is_mcp_request(scope) is False


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_different_case_headers(mock_asgi_transport, mock_lihil_mcp):
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {
        "type": "http", 
        "path": "/api/test",
        "headers": [
            (b"Content-Type", b"APPLICATION/JSON"),
            (b"X-JSONRPC", b"2.0")
        ]
    }
    
    # Current implementation is case-sensitive for header values
    assert transport._is_mcp_request(scope) is False


@patch('lihil_mcp.transport.ASGIServerTransport')
def test_is_mcp_request_multiple_content_type_values(mock_asgi_transport, mock_lihil_mcp):
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {
        "type": "http", 
        "path": "/api/test",
        "headers": [
            (b"content-type", b"text/html"),
            (b"content-type", b"application/json; jsonrpc=2.0")
        ]
    }
    
    # This tests how the implementation handles multiple content-type headers
    # The dict() conversion will use the last value
    assert transport._is_mcp_request(scope) is True


def test_mcp_middleware_init():
    mock_app = Mock()
    mock_mcp_transport = Mock()
    
    middleware = MCPMiddleware(mock_app, mock_mcp_transport)
    
    assert middleware.app == mock_app
    assert middleware.mcp_transport == mock_mcp_transport


@pytest.mark.asyncio
async def test_mcp_middleware_call():
    mock_app = AsyncMock()
    mock_mcp_transport = AsyncMock()
    
    middleware = MCPMiddleware(mock_app, mock_mcp_transport)
    
    scope = {"type": "http", "path": "/test"}
    receive = AsyncMock()
    send = AsyncMock()
    
    await middleware(scope, receive, send)
    
    mock_mcp_transport.assert_called_once_with(scope, receive, send)
    mock_app.assert_not_called()


@patch('lihil_mcp.transport.ASGIServerTransport')
@pytest.mark.asyncio
async def test_transport_exception_handling(mock_asgi_transport, mock_lihil_mcp):
    mock_transport_instance = AsyncMock()
    mock_transport_instance.side_effect = Exception("Transport error")
    mock_asgi_transport.return_value = mock_transport_instance
    
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {"type": "http", "path": "/mcp/test"}
    receive = AsyncMock()
    send = AsyncMock()
    
    # The implementation doesn't explicitly handle exceptions, 
    # so they should propagate
    with pytest.raises(Exception, match="Transport error"):
        await transport(scope, receive, send)


@patch('lihil_mcp.transport.ASGIServerTransport')
@pytest.mark.asyncio
async def test_app_exception_handling(mock_asgi_transport, mock_lihil_mcp):
    mock_transport_instance = AsyncMock()
    mock_asgi_transport.return_value = mock_transport_instance
    
    mock_lihil_mcp.app.side_effect = Exception("App error")
    
    transport = LihilMCPTransport(mock_lihil_mcp)
    
    scope = {"type": "http", "path": "/api/test"}
    receive = AsyncMock()
    send = AsyncMock()
    
    # The implementation doesn't explicitly handle exceptions, 
    # so they should propagate
    with pytest.raises(Exception, match="App error"):
        await transport(scope, receive, send)


@pytest.mark.asyncio
async def test_mcp_middleware_exception_handling():
    mock_app = AsyncMock()
    mock_mcp_transport = AsyncMock()
    mock_mcp_transport.side_effect = Exception("Middleware error")
    
    middleware = MCPMiddleware(mock_app, mock_mcp_transport)
    
    scope = {"type": "http", "path": "/test"}
    receive = AsyncMock()
    send = AsyncMock()
    
    # The implementation doesn't explicitly handle exceptions, 
    # so they should propagate
    with pytest.raises(Exception, match="Middleware error"):
        await middleware(scope, receive, send)


# Test for import error coverage (lines 9-10)
def test_transport_import_error():
    """Test that MissingDependencyError is raised when MCP imports fail in transport."""
    import sys
    # We need to patch the import at module level, and trigger a fresh import
    with patch.dict('sys.modules', {'mcp.server.sse': None}):
        # Clear any cached imports
        if 'lihil_mcp.transport' in sys.modules:
            del sys.modules['lihil_mcp.transport']
        
        # Now import should fail and trigger the exception
        from lihil.errors import MissingDependencyError
        with pytest.raises(MissingDependencyError):
            import lihil_mcp.transport