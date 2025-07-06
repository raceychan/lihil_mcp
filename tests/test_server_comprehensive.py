import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import inspect
import json

from lihil_mcp.server import LihilMCP
from lihil_mcp.config import MCPConfig
from lihil_mcp.types import MCPError, MCPRegistrationError, MCPToolInfo, MCPResourceInfo
from lihil_mcp.decorators import mcp_tool, mcp_resource


class MockEndpoint:
    def __init__(self, func, method="GET"):
        self.unwrapped_func = func
        self.method = method


class MockRoute:
    def __init__(self, path="/test", endpoints=None):
        self.path = path
        self.endpoints = endpoints or {}


class MockApp:
    def __init__(self, routes=None):
        self.routes = routes or []


@pytest.fixture
def mock_app():
    return MockApp()


@pytest.fixture
def config():
    return MCPConfig(server_name="test-server", auto_expose=False)


@pytest.fixture
def auto_expose_config():
    return MCPConfig(server_name="test-server", auto_expose=True)


@patch('lihil_mcp.server.FastMCP')
def test_lihil_mcp_init(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_mcp_server.tool = Mock()
    mock_mcp_server.resource = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    assert lihil_mcp.app == mock_app
    assert lihil_mcp.config == config
    assert lihil_mcp.mcp_server == mock_mcp_server
    mock_fastmcp.assert_called_once_with("test-server")


@patch('lihil_mcp.server.FastMCP')
def test_register_mcp_tool(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_tool_decorator = Mock()
    mock_mcp_server.tool = Mock(return_value=mock_tool_decorator)
    mock_fastmcp.return_value = mock_mcp_server
    
    @mcp_tool(description="Test tool")
    def test_func(param1: str, param2: int = 10):
        return {"result": f"{param1}_{param2}"}
    
    endpoint = MockEndpoint(test_func)
    route = MockRoute("/test", {"GET": endpoint})
    mock_app.routes = [route]
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    assert "test_func" in lihil_mcp._tools
    tool_info = lihil_mcp._tools["test_func"]
    assert tool_info.name == "test_func"
    assert tool_info.description == "Test tool"
    assert "param1" in tool_info.inputSchema["properties"]
    assert "param2" in tool_info.inputSchema["properties"]
    assert "param1" in tool_info.inputSchema["required"]
    assert "param2" not in tool_info.inputSchema["required"]
    
    mock_mcp_server.tool.assert_called()


@patch('lihil_mcp.server.FastMCP')
def test_register_mcp_resource(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_resource_decorator = Mock()
    mock_mcp_server.resource = Mock(return_value=mock_resource_decorator)
    mock_fastmcp.return_value = mock_mcp_server
    
    @mcp_resource(uri_template="test://resource", title="Test Resource")
    def test_resource():
        return {"data": "test"}
    
    endpoint = MockEndpoint(test_resource)
    route = MockRoute("/test", {"GET": endpoint})
    mock_app.routes = [route]
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    assert "test://resource" in lihil_mcp._resources
    resource_info = lihil_mcp._resources["test://resource"]
    assert resource_info.name == "Test Resource"
    assert resource_info.uri == "test://resource"
    
    mock_mcp_server.resource.assert_called()


@patch('lihil_mcp.server.FastMCP')
def test_auto_expose_tool_post_method(mock_fastmcp, mock_app, auto_expose_config):
    mock_mcp_server = Mock()
    mock_tool_decorator = Mock()
    mock_mcp_server.tool = Mock(return_value=mock_tool_decorator)
    mock_fastmcp.return_value = mock_mcp_server
    
    def test_func():
        return {"result": "test"}
    
    endpoint = MockEndpoint(test_func, "POST")
    route = MockRoute("/test", {"POST": endpoint})
    mock_app.routes = [route]
    
    lihil_mcp = LihilMCP(mock_app, auto_expose_config)
    
    assert "test_func" in lihil_mcp._tools
    tool_info = lihil_mcp._tools["test_func"]
    assert "Auto-exposed tool" in tool_info.description


@patch('lihil_mcp.server.FastMCP')
def test_auto_expose_tool_put_method(mock_fastmcp, mock_app, auto_expose_config):
    mock_mcp_server = Mock()
    mock_tool_decorator = Mock()
    mock_mcp_server.tool = Mock(return_value=mock_tool_decorator)
    mock_fastmcp.return_value = mock_mcp_server
    
    def test_func():
        return {"result": "test"}
    
    endpoint = MockEndpoint(test_func, "PUT")
    route = MockRoute("/test", {"PUT": endpoint})
    mock_app.routes = [route]
    
    lihil_mcp = LihilMCP(mock_app, auto_expose_config)
    
    assert "test_func" in lihil_mcp._tools


@patch('lihil_mcp.server.FastMCP')
def test_auto_expose_tool_patch_method(mock_fastmcp, mock_app, auto_expose_config):
    mock_mcp_server = Mock()
    mock_tool_decorator = Mock()
    mock_mcp_server.tool = Mock(return_value=mock_tool_decorator)
    mock_fastmcp.return_value = mock_mcp_server
    
    def test_func():
        return {"result": "test"}
    
    endpoint = MockEndpoint(test_func, "PATCH")
    route = MockRoute("/test", {"PATCH": endpoint})
    mock_app.routes = [route]
    
    lihil_mcp = LihilMCP(mock_app, auto_expose_config)
    
    assert "test_func" in lihil_mcp._tools


@patch('lihil_mcp.server.FastMCP')
def test_auto_expose_resource_get_method(mock_fastmcp, mock_app, auto_expose_config):
    mock_mcp_server = Mock()
    mock_resource_decorator = Mock()
    mock_mcp_server.resource = Mock(return_value=mock_resource_decorator)
    mock_fastmcp.return_value = mock_mcp_server
    
    def test_func():
        return {"data": "test"}
    
    endpoint = MockEndpoint(test_func, "GET")
    route = MockRoute("/test", {"GET": endpoint})
    mock_app.routes = [route]
    
    lihil_mcp = LihilMCP(mock_app, auto_expose_config)
    
    assert "lihil://test" in lihil_mcp._resources
    resource_info = lihil_mcp._resources["lihil://test"]
    assert "Auto-exposed resource" in resource_info.description


@patch('lihil_mcp.server.FastMCP')
def test_registration_error_during_setup(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_mcp_server.tool = Mock(side_effect=Exception("Tool registration failed"))
    mock_fastmcp.return_value = mock_mcp_server
    
    @mcp_tool(description="Test tool")
    def problematic_func():
        pass
    
    endpoint = MockEndpoint(problematic_func)
    route = MockRoute("/test", {"GET": endpoint})
    mock_app.routes = [route]
    
    with pytest.raises(MCPRegistrationError):
        LihilMCP(mock_app, config)


@patch('lihil_mcp.server.FastMCP')
def test_generate_input_schema_with_different_types(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_mcp_server.tool = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    def test_func(string_param: str, int_param: int, float_param: float, 
                  bool_param: bool, list_param: list, dict_param: dict,
                  no_annotation, optional_param: str = "default"):
        pass
    
    schema = lihil_mcp._generate_input_schema(test_func)
    
    assert schema["type"] == "object"
    assert schema["properties"]["string_param"]["type"] == "string"
    assert schema["properties"]["int_param"]["type"] == "integer"
    assert schema["properties"]["float_param"]["type"] == "number"
    assert schema["properties"]["bool_param"]["type"] == "boolean"
    assert schema["properties"]["list_param"]["type"] == "array"
    assert schema["properties"]["dict_param"]["type"] == "object"
    assert schema["properties"]["no_annotation"]["type"] == "string"  # defaults to string
    assert schema["properties"]["optional_param"]["type"] == "string"
    
    required_params = schema["required"]
    assert "string_param" in required_params
    assert "int_param" in required_params
    assert "float_param" in required_params
    assert "bool_param" in required_params
    assert "list_param" in required_params
    assert "dict_param" in required_params
    assert "no_annotation" in required_params
    assert "optional_param" not in required_params  # has default value


@patch('lihil_mcp.server.FastMCP')
def test_generate_input_schema_no_parameters(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    def test_func():
        pass
    
    schema = lihil_mcp._generate_input_schema(test_func)
    assert schema is None


@patch('lihil_mcp.server.FastMCP')
def test_generate_input_schema_ignores_self_and_cls(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    def test_method(self, cls, param: str):
        pass
    
    schema = lihil_mcp._generate_input_schema(test_method)
    
    assert "self" not in schema["properties"]
    assert "cls" not in schema["properties"]
    assert "param" in schema["properties"]


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_call_endpoint_sync_function(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    def test_func(param1: str, param2: int = 10):
        return {"result": f"{param1}_{param2}"}
    
    endpoint = MockEndpoint(test_func)
    route = MockRoute("/test", {"GET": endpoint})
    
    lihil_mcp = LihilMCP(mock_app, config)
    lihil_mcp._endpoint_map["test_func"] = (route, endpoint)
    
    result = await lihil_mcp._call_endpoint("test_func", {"param1": "hello", "param2": 20})
    assert result == {"result": "hello_20"}


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_call_endpoint_async_function(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    async def test_func(param1: str):
        return {"result": param1}
    
    endpoint = MockEndpoint(test_func)
    route = MockRoute("/test", {"GET": endpoint})
    
    lihil_mcp = LihilMCP(mock_app, config)
    lihil_mcp._endpoint_map["test_func"] = (route, endpoint)
    
    result = await lihil_mcp._call_endpoint("test_func", {"param1": "hello"})
    assert result == {"result": "hello"}


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_call_endpoint_with_defaults(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    def test_func(param1: str, param2: int = 42):
        return {"result": f"{param1}_{param2}"}
    
    endpoint = MockEndpoint(test_func)
    route = MockRoute("/test", {"GET": endpoint})
    
    lihil_mcp = LihilMCP(mock_app, config)
    lihil_mcp._endpoint_map["test_func"] = (route, endpoint)
    
    # Call without param2, should use default
    result = await lihil_mcp._call_endpoint("test_func", {"param1": "hello"})
    assert result == {"result": "hello_42"}


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_call_endpoint_not_found(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    with pytest.raises(MCPError, match="Tool nonexistent not found"):
        await lihil_mcp._call_endpoint("nonexistent", {})


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_call_endpoint_function_error(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    def test_func():
        raise ValueError("Test error")
    
    endpoint = MockEndpoint(test_func)
    route = MockRoute("/test", {"GET": endpoint})
    
    lihil_mcp = LihilMCP(mock_app, config)
    lihil_mcp._endpoint_map["test_func"] = (route, endpoint)
    
    with pytest.raises(MCPError, match="Error calling endpoint test_func"):
        await lihil_mcp._call_endpoint("test_func", {})


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_call_endpoint_non_json_serializable_result(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    class CustomObject:
        def __str__(self):
            return "custom_object"
    
    def test_func():
        return CustomObject()
    
    endpoint = MockEndpoint(test_func)
    route = MockRoute("/test", {"GET": endpoint})
    
    lihil_mcp = LihilMCP(mock_app, config)
    lihil_mcp._endpoint_map["test_func"] = (route, endpoint)
    
    result = await lihil_mcp._call_endpoint("test_func", {})
    assert result == "custom_object"


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_call_endpoint_as_resource_sync(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    def test_resource():
        return {"data": "test"}
    
    endpoint = MockEndpoint(test_resource)
    route = MockRoute("/test", {"GET": endpoint})
    
    lihil_mcp = LihilMCP(mock_app, config)
    lihil_mcp._endpoint_map["test://resource"] = (route, endpoint)
    
    result = await lihil_mcp._call_endpoint_as_resource("test://resource")
    assert result == {"data": "test"}


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_call_endpoint_as_resource_async(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    async def test_resource():
        return {"data": "async"}
    
    endpoint = MockEndpoint(test_resource)
    route = MockRoute("/test", {"GET": endpoint})
    
    lihil_mcp = LihilMCP(mock_app, config)
    lihil_mcp._endpoint_map["test://resource"] = (route, endpoint)
    
    result = await lihil_mcp._call_endpoint_as_resource("test://resource")
    assert result == {"data": "async"}


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_call_endpoint_as_resource_not_found(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    with pytest.raises(MCPError, match="Resource nonexistent not found"):
        await lihil_mcp._call_endpoint_as_resource("nonexistent")


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_call_endpoint_as_resource_error(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    def test_resource():
        raise ValueError("Resource error")
    
    endpoint = MockEndpoint(test_resource)
    route = MockRoute("/test", {"GET": endpoint})
    
    lihil_mcp = LihilMCP(mock_app, config)
    lihil_mcp._endpoint_map["test://resource"] = (route, endpoint)
    
    with pytest.raises(MCPError, match="Error accessing resource test://resource"):
        await lihil_mcp._call_endpoint_as_resource("test://resource")


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_call_endpoint_as_resource_non_json_serializable(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    class CustomResource:
        def __str__(self):
            return "custom_resource"
    
    def test_resource():
        return CustomResource()
    
    endpoint = MockEndpoint(test_resource)
    route = MockRoute("/test", {"GET": endpoint})
    
    lihil_mcp = LihilMCP(mock_app, config)
    lihil_mcp._endpoint_map["test://resource"] = (route, endpoint)
    
    result = await lihil_mcp._call_endpoint_as_resource("test://resource")
    assert result == "custom_resource"


@patch('lihil_mcp.server.FastMCP')
def test_tools_property(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    lihil_mcp = LihilMCP(mock_app, config)
    tool_info = MCPToolInfo(name="test", description="Test tool", inputSchema={})
    lihil_mcp._tools["test"] = tool_info
    
    tools = lihil_mcp.tools
    assert "test" in tools
    assert tools["test"] == tool_info
    # Ensure it's a copy
    assert tools is not lihil_mcp._tools


@patch('lihil_mcp.server.FastMCP')
def test_resources_property(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    lihil_mcp = LihilMCP(mock_app, config)
    resource_info = MCPResourceInfo(uri="test://resource", name="Test", description="Test resource")
    lihil_mcp._resources["test://resource"] = resource_info
    
    resources = lihil_mcp.resources
    assert "test://resource" in resources
    assert resources["test://resource"] == resource_info
    # Ensure it's a copy
    assert resources is not lihil_mcp._resources


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_handle_mcp_request(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    # Test that the method exists and doesn't raise an error
    scope = {"type": "http", "path": "/mcp"}
    receive = AsyncMock()
    send = AsyncMock()
    
    await lihil_mcp.handle_mcp_request(scope, receive, send)
    # Method currently just passes, so no assertions needed


@patch('lihil_mcp.server.FastMCP')
def test_mcp_resource_with_extra_mime_type(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_resource_decorator = Mock()
    mock_mcp_server.resource = Mock(return_value=mock_resource_decorator)
    mock_fastmcp.return_value = mock_mcp_server
    
    @mcp_resource(uri_template="test://resource", title="Test Resource", mime_type="text/plain")
    def test_resource():
        return "plain text"
    
    endpoint = MockEndpoint(test_resource)
    route = MockRoute("/test", {"GET": endpoint})
    mock_app.routes = [route]
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    resource_info = lihil_mcp._resources["test://resource"]
    assert resource_info.mimeType == "text/plain"


@patch('lihil_mcp.server.FastMCP')
def test_auto_expose_resource_with_complex_path(mock_fastmcp, mock_app, auto_expose_config):
    mock_mcp_server = Mock()
    mock_resource_decorator = Mock()
    mock_mcp_server.resource = Mock(return_value=mock_resource_decorator)
    mock_fastmcp.return_value = mock_mcp_server
    
    def test_func():
        return {"data": "test"}
    
    endpoint = MockEndpoint(test_func, "GET")
    route = MockRoute("/api/v1/users/profile", {"GET": endpoint})
    mock_app.routes = [route]
    
    lihil_mcp = LihilMCP(mock_app, auto_expose_config)
    
    assert "lihil://api_v1_users_profile" in lihil_mcp._resources


# Test for import error coverage (lines 22-23)
def test_import_error():
    """Test that MissingDependencyError is raised when MCP imports fail."""
    import sys
    # We need to patch the import at module level, and trigger a fresh import
    with patch.dict('sys.modules', {'mcp.server.fastmcp': None}):
        # Clear any cached imports
        if 'lihil_mcp.server' in sys.modules:
            del sys.modules['lihil_mcp.server']
        
        # Now import should fail and trigger the exception
        from lihil.errors import MissingDependencyError
        with pytest.raises(MissingDependencyError):
            import lihil_mcp.server


# Test for missing routes attribute (line 46)
@patch('lihil_mcp.server.FastMCP')
def test_app_without_routes_attribute(mock_fastmcp, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    # Create an app without routes attribute
    mock_app = Mock(spec=[])  # spec=[] means no attributes
    
    # This should not raise an error and should just return early
    lihil_mcp = LihilMCP(mock_app, config)
    assert lihil_mcp.app == mock_app


# Test for schema generation exception (lines 200-201)
@patch('lihil_mcp.server.FastMCP')
def test_generate_input_schema_exception_handling(mock_fastmcp, mock_app, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    # Test with something that will cause inspect.signature to fail
    problematic_input = "not a function"
    
    schema = lihil_mcp._generate_input_schema(problematic_input)
    assert schema is None


# Test the actual wrapper functions (lines 94, 120, 142, 158) by simulating their execution
@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_mcp_tool_wrapper_execution(mock_fastmcp, mock_app, config):
    """Test that the MCP tool wrapper functions are properly created and called."""
    mock_mcp_server = Mock()
    
    # Capture the wrapper function
    captured_wrapper = None
    def capture_tool_decorator(name, description):
        def decorator(func):
            nonlocal captured_wrapper
            captured_wrapper = func
            return func
        return decorator
    
    mock_mcp_server.tool = capture_tool_decorator
    mock_fastmcp.return_value = mock_mcp_server
    
    @mcp_tool(description="Test tool")
    def test_func(param: str):
        return {"result": param}
    
    endpoint = MockEndpoint(test_func)
    route = MockRoute("/test", {"GET": endpoint})
    mock_app.routes = [route]
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    # The wrapper should have been captured
    assert captured_wrapper is not None
    
    # Call the wrapper - this tests line 94
    result = await captured_wrapper(param="test")
    assert result == {"result": "test"}


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_mcp_resource_wrapper_execution(mock_fastmcp, mock_app, config):
    """Test that the MCP resource wrapper functions are properly created and called."""
    mock_mcp_server = Mock()
    
    # Capture the wrapper function
    captured_wrapper = None
    def capture_resource_decorator(uri):
        def decorator(func):
            nonlocal captured_wrapper
            captured_wrapper = func
            return func
        return decorator
    
    mock_mcp_server.resource = capture_resource_decorator
    mock_fastmcp.return_value = mock_mcp_server
    
    @mcp_resource(uri_template="test://resource", title="Test Resource")
    def test_resource():
        return {"data": "test"}
    
    endpoint = MockEndpoint(test_resource)
    route = MockRoute("/test", {"GET": endpoint})
    mock_app.routes = [route]
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    # The wrapper should have been captured
    assert captured_wrapper is not None
    
    # Call the wrapper - this tests line 120
    result = await captured_wrapper()
    assert result == {"data": "test"}


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_auto_tool_wrapper_execution(mock_fastmcp, mock_app, auto_expose_config):
    """Test that the auto-exposed tool wrapper functions are properly created and called."""
    mock_mcp_server = Mock()
    
    # Capture the wrapper function
    captured_wrapper = None
    def capture_tool_decorator(name, description):
        def decorator(func):
            nonlocal captured_wrapper
            captured_wrapper = func
            return func
        return decorator
    
    mock_mcp_server.tool = capture_tool_decorator
    mock_fastmcp.return_value = mock_mcp_server
    
    def test_func(param: str):
        return {"result": param}
    
    endpoint = MockEndpoint(test_func, "POST")
    route = MockRoute("/test", {"POST": endpoint})
    mock_app.routes = [route]
    
    lihil_mcp = LihilMCP(mock_app, auto_expose_config)
    
    # The wrapper should have been captured
    assert captured_wrapper is not None
    
    # Call the wrapper - this tests line 142
    result = await captured_wrapper(param="test")
    assert result == {"result": "test"}


@patch('lihil_mcp.server.FastMCP')
@pytest.mark.asyncio
async def test_auto_resource_wrapper_execution(mock_fastmcp, mock_app, auto_expose_config):
    """Test that the auto-exposed resource wrapper functions are properly created and called."""
    mock_mcp_server = Mock()
    
    # Capture the wrapper function
    captured_wrapper = None
    def capture_resource_decorator(uri):
        def decorator(func):
            nonlocal captured_wrapper
            captured_wrapper = func
            return func
        return decorator
    
    mock_mcp_server.resource = capture_resource_decorator
    mock_fastmcp.return_value = mock_mcp_server
    
    def test_func():
        return {"data": "test"}
    
    endpoint = MockEndpoint(test_func, "GET")
    route = MockRoute("/test", {"GET": endpoint})
    mock_app.routes = [route]
    
    lihil_mcp = LihilMCP(mock_app, auto_expose_config)
    
    # The wrapper should have been captured
    assert captured_wrapper is not None
    
    # Call the wrapper - this tests line 158
    result = await captured_wrapper()
    assert result == {"data": "test"}