import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import inspect
import json

from lihil import Lihil
from lihil.routing import Route
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
    
    async def __call__(self, scope, receive, send):
        """Mock ASGI callable."""
        pass


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
    lihil_mcp.setup_mcp_tools_and_resources()
    
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
    lihil_mcp.setup_mcp_tools_and_resources()
    
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
    lihil_mcp.setup_mcp_tools_and_resources()
    
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
    lihil_mcp.setup_mcp_tools_and_resources()
    
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
    lihil_mcp.setup_mcp_tools_and_resources()
    
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
    lihil_mcp.setup_mcp_tools_and_resources()
    
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
    
    lihil_mcp = LihilMCP(mock_app, config)
    with pytest.raises(MCPRegistrationError):
        lihil_mcp.setup_mcp_tools_and_resources()


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
    lihil_mcp._endpoint_map["test_func"] = endpoint
    
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
    lihil_mcp._endpoint_map["test_func"] = endpoint
    
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
    lihil_mcp._endpoint_map["test_func"] = endpoint
    
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
    lihil_mcp._endpoint_map["test_func"] = endpoint
    
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
    lihil_mcp._endpoint_map["test_func"] = endpoint
    
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
    lihil_mcp._endpoint_map["test://resource"] = endpoint
    
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
    lihil_mcp._endpoint_map["test://resource"] = endpoint
    
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
    lihil_mcp._endpoint_map["test://resource"] = endpoint
    
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
    lihil_mcp._endpoint_map["test://resource"] = endpoint
    
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
async def test_asgi_http_request(mock_fastmcp, config):
    mock_mcp_server = Mock()
    mock_fastmcp.return_value = mock_mcp_server
    
    # Create a mock app with a tracked __call__ method
    mock_app = AsyncMock()
    mock_app.routes = []
    
    lihil_mcp = LihilMCP(mock_app, config)
    
    # Test that ASGI HTTP requests are forwarded to the Lihil app
    scope = {"type": "http", "path": "/test"}
    receive = AsyncMock()
    send = AsyncMock()
    
    await lihil_mcp(scope, receive, send)
    
    # Verify that the request was forwarded to the Lihil app
    mock_app.assert_called_once_with(scope, receive, send)


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
    lihil_mcp.setup_mcp_tools_and_resources()
    
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
    lihil_mcp.setup_mcp_tools_and_resources()
    
    assert "lihil://api_v1_users_profile" in lihil_mcp._resources




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
    lihil_mcp.setup_mcp_tools_and_resources()
    
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
    lihil_mcp.setup_mcp_tools_and_resources()
    
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
    lihil_mcp.setup_mcp_tools_and_resources()
    
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
    lihil_mcp.setup_mcp_tools_and_resources()
    
    # The wrapper should have been captured
    assert captured_wrapper is not None
    
    # Call the wrapper - this tests line 158
    result = await captured_wrapper()
    assert result == {"data": "test"}


# Tests using real Lihil applications instead of mocks

def test_real_mcp_tool_registration():
    """Test MCP tool registration with real Lihil application."""
    route = Route("/api")
    
    @route.post
    @mcp_tool(description="Create a user with real implementation")
    def create_user(name: str, email: str = "test@example.com"):
        return {"id": 1, "name": name, "email": email, "created": True}
    
    app = Lihil(route)
    config = MCPConfig(server_name="test-real-app")
    lihil_mcp = LihilMCP(app, config)
    lihil_mcp.setup_mcp_tools_and_resources()
    
    # Verify tool registration
    assert "create_user" in lihil_mcp.tools
    tool_info = lihil_mcp.tools["create_user"]
    assert tool_info.name == "create_user"
    assert "Create a user with real implementation" in tool_info.description
    assert tool_info.inputSchema is not None
    assert "name" in tool_info.inputSchema["properties"]
    assert "email" in tool_info.inputSchema["properties"]
    assert "name" in tool_info.inputSchema["required"]
    assert "email" not in tool_info.inputSchema["required"]  # Has default


def test_real_mcp_resource_registration():
    """Test MCP resource registration with real Lihil application."""
    route = Route("/status")
    
    @route.get
    @mcp_resource(uri_template="lihil://system-status", description="System status endpoint")
    def get_status():
        return {"status": "healthy", "uptime": "100%"}
    
    app = Lihil(route)
    config = MCPConfig(server_name="test-real-app")
    lihil_mcp = LihilMCP(app, config)
    lihil_mcp.setup_mcp_tools_and_resources()
    
    # Verify resource registration
    assert "lihil://system-status" in lihil_mcp.resources
    resource_info = lihil_mcp.resources["lihil://system-status"]
    assert resource_info.uri == "lihil://system-status"
    assert resource_info.description == "System status endpoint"
    assert resource_info.mimeType == "application/json"


def test_real_auto_expose_functionality():
    """Test auto-expose functionality with real Lihil application."""
    route = Route("/data")
    
    @route.get
    def get_data():
        """Retrieve system data."""
        return {"data": [1, 2, 3, 4, 5]}
    
    @route.post
    def process_data(input_data: str):
        """Process input data."""
        return {"processed": input_data.upper(), "length": len(input_data)}
    
    app = Lihil(route)
    config = MCPConfig(server_name="test-auto-expose", auto_expose=True)
    lihil_mcp = LihilMCP(app, config)
    lihil_mcp.setup_mcp_tools_and_resources()
    
    # Verify auto-exposed tool (POST)
    assert "process_data" in lihil_mcp.tools
    tool_info = lihil_mcp.tools["process_data"]
    # Function has docstring, so that's used instead of "Auto-exposed tool"
    assert tool_info.description == "Process input data."
    
    # Verify auto-exposed resource (GET)
    assert "lihil://data" in lihil_mcp.resources
    resource_info = lihil_mcp.resources["lihil://data"]
    # Function has docstring, so that's used instead of "Auto-exposed resource"
    assert resource_info.description == "Retrieve system data."


@pytest.mark.asyncio
async def test_real_endpoint_execution():
    """Test actual endpoint execution through MCP with real Lihil application."""
    route = Route("/math")
    
    @route.post
    @mcp_tool(description="Add two numbers")
    def add_numbers(a: int, b: int):
        return {"result": a + b, "operation": "addition"}
    
    @route.get
    @mcp_resource(uri_template="lihil://math-constants")
    def get_constants():
        return {"pi": 3.14159, "e": 2.71828}
    
    app = Lihil(route)
    config = MCPConfig(server_name="test-math-app")
    lihil_mcp = LihilMCP(app, config)
    lihil_mcp.setup_mcp_tools_and_resources()
    
    # Test tool execution
    result = await lihil_mcp._call_endpoint("add_numbers", {"a": 5, "b": 3})
    assert result == {"result": 8, "operation": "addition"}
    
    # Test resource execution
    result = await lihil_mcp._call_endpoint_as_resource("lihil://math-constants")
    assert result == {"pi": 3.14159, "e": 2.71828}


@pytest.mark.asyncio
async def test_real_async_endpoint():
    """Test async endpoint execution with real Lihil application."""
    route = Route("/async")
    
    @route.post
    @mcp_tool(description="Async data processor")
    async def process_async(data: str):
        # Simulate some async work
        return {"processed": f"ASYNC_{data}", "async": True}
    
    app = Lihil(route)
    config = MCPConfig(server_name="test-async-app")
    lihil_mcp = LihilMCP(app, config)
    lihil_mcp.setup_mcp_tools_and_resources()
    
    # Test async endpoint execution
    result = await lihil_mcp._call_endpoint("process_async", {"data": "test"})
    assert result == {"processed": "ASYNC_test", "async": True}


def test_real_error_handling():
    """Test error handling with real Lihil application."""
    route = Route("/error")
    
    @route.post
    @mcp_tool(description="Function that raises an error")
    def error_function(should_error: bool):
        if should_error:
            raise ValueError("Intentional test error")
        return {"success": True}
    
    app = Lihil(route)
    config = MCPConfig(server_name="test-error-app")
    lihil_mcp = LihilMCP(app, config)
    lihil_mcp.setup_mcp_tools_and_resources()
    
    # Test that function is registered
    assert "error_function" in lihil_mcp.tools
    
    # Test error propagation (this would be tested in integration tests)
    # The actual error handling is tested in the integration tests with real execution


def test_real_complex_types():
    """Test complex type handling with real Lihil application."""
    route = Route("/complex")
    
    @route.post
    @mcp_tool(description="Handle complex data types")
    def handle_complex(
        numbers: list,
        metadata: dict,
        optional_flag: bool = False
    ):
        return {
            "numbers_sum": sum(numbers) if numbers else 0,
            "metadata_keys": list(metadata.keys()) if metadata else [],
            "flag_set": optional_flag
        }
    
    app = Lihil(route)
    config = MCPConfig(server_name="test-complex-app")
    lihil_mcp = LihilMCP(app, config)
    lihil_mcp.setup_mcp_tools_and_resources()
    
    # Verify tool registration
    assert "handle_complex" in lihil_mcp.tools
    tool_info = lihil_mcp.tools["handle_complex"]
    
    # Verify schema generation for complex types
    schema = tool_info.inputSchema
    assert schema["properties"]["numbers"]["type"] == "array"
    assert schema["properties"]["metadata"]["type"] == "object"
    assert schema["properties"]["optional_flag"]["type"] == "boolean"
    assert "numbers" in schema["required"]
    assert "metadata" in schema["required"]
    assert "optional_flag" not in schema["required"]