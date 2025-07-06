"""Main MCP server implementation for lihil."""

import inspect
import json
from typing import Dict, List, Optional, Union

from lihil import Lihil
from lihil.errors import MissingDependencyError

from .config import MCPConfig
from .decorators import get_mcp_metadata, is_mcp_endpoint
from .types import (
    MCPError,
    MCPMetadata,
    MCPRegistrationError,
    MCPResourceInfo,
    MCPToolInfo,
)

try:
    from mcp.server.fastmcp import FastMCP, Context
except ImportError as e:
    raise MissingDependencyError("mcp") from e


class LihilMCP:
    """MCP server integration for lihil applications."""

    def __init__(self, app: "Lihil", config: MCPConfig):  # app is Lihil instance

        self.app = app
        self.config = config
        self.mcp_server = FastMCP(config.server_name)
        self._tools: Dict[str, MCPToolInfo] = {}
        self._resources: Dict[str, MCPResourceInfo] = {}
        self._endpoint_map: Dict[str, tuple["RouteBase", "Endpoint"]] = (
            {}
        )  # RouteBase, Endpoint

        # Setup MCP tools and resources
        self._setup_mcp_endpoints()

    def _setup_mcp_endpoints(self) -> None:
        """Convert lihil routes to MCP tools and resources."""
        if not hasattr(self.app, "routes"):
            return

        for route in self.app.routes:
            if hasattr(route, "endpoints"):
                for method, endpoint in route.endpoints.items():
                    try:
                        self._register_endpoint(route, endpoint)
                    except Exception as e:
                        raise MCPRegistrationError(
                            f"Failed to register endpoint {endpoint.unwrapped_func.__name__}: {e}"
                        ) from e

    def _register_endpoint(
        self, route: "RouteBase", endpoint: "Endpoint"
    ) -> None:  # route is RouteBase
        """Register a lihil endpoint as MCP tool or resource."""
        func = endpoint.unwrapped_func
        mcp_meta = get_mcp_metadata(func)

        if mcp_meta:
            if mcp_meta.type == "tool":
                self._register_as_tool(route, endpoint, mcp_meta)
            elif mcp_meta.type == "resource":
                self._register_as_resource(route, endpoint, mcp_meta)
        elif self.config.auto_expose:
            self._auto_register_endpoint(route, endpoint)

    def _register_as_tool(
        self, route: "RouteBase", endpoint: "Endpoint", mcp_meta: "MCPMetadata"
    ) -> None:  # route is RouteBase
        """Register an endpoint as an MCP tool."""
        func = endpoint.unwrapped_func
        func_name = func.__name__

        # Create tool info
        tool_info = MCPToolInfo(
            name=func_name,
            description=mcp_meta.description or func.__doc__ or f"Tool: {func_name}",
            inputSchema=self._generate_input_schema(func),
        )

        self._tools[func_name] = tool_info
        self._endpoint_map[func_name] = (route, endpoint)

        # Register with FastMCP
        @self.mcp_server.tool(name=func_name, description=tool_info.description)
        async def mcp_tool_wrapper(**kwargs):
            """Wrapper to call the actual lihil endpoint."""
            return await self._call_endpoint(func_name, kwargs)

    def _register_as_resource(
        self, route: "RouteBase", endpoint: "Endpoint", mcp_meta: "MCPMetadata"
    ) -> None:  # route is RouteBase
        """Register an endpoint as an MCP resource."""
        func = endpoint.unwrapped_func
        func_name = func.__name__

        # Create resource info
        resource_info = MCPResourceInfo(
            uri=mcp_meta.uri_template or f"lihil://{func_name}",
            name=mcp_meta.title or func_name,
            description=mcp_meta.description
            or func.__doc__
            or f"Resource: {func_name}",
            mimeType=mcp_meta.extra.get("mime_type", "application/json"),
        )

        self._resources[resource_info.uri] = resource_info
        self._endpoint_map[resource_info.uri] = (route, endpoint)

        # Register with FastMCP
        @self.mcp_server.resource(uri=resource_info.uri)
        async def mcp_resource_wrapper():
            """Wrapper to call the actual lihil endpoint."""
            return await self._call_endpoint_as_resource(resource_info.uri)

    def _auto_register_endpoint(
        self, route: "RouteBase", endpoint: "Endpoint"
    ) -> None:  # route is RouteBase
        """Automatically register an endpoint based on HTTP method."""
        func = endpoint.unwrapped_func
        func_name = func.__name__
        method = endpoint.method

        if method.upper() in ["POST", "PUT", "PATCH"]:
            # Register as tool
            tool_info = MCPToolInfo(
                name=func_name,
                description=func.__doc__ or f"Auto-exposed tool: {func_name}",
                inputSchema=self._generate_input_schema(func),
            )
            self._tools[func_name] = tool_info
            self._endpoint_map[func_name] = (route, endpoint)

            @self.mcp_server.tool(name=func_name, description=tool_info.description)
            async def mcp_auto_tool_wrapper(**kwargs):
                return await self._call_endpoint(func_name, kwargs)

        elif method.upper() == "GET":
            # Register as resource
            resource_uri = f"lihil://{route.path.replace('/', '_').strip('_')}"
            resource_info = MCPResourceInfo(
                uri=resource_uri,
                name=func_name,
                description=func.__doc__ or f"Auto-exposed resource: {func_name}",
                mimeType="application/json",
            )
            self._resources[resource_uri] = resource_info
            self._endpoint_map[resource_uri] = (route, endpoint)

            @self.mcp_server.resource(uri=resource_uri)
            async def mcp_auto_resource_wrapper():
                return await self._call_endpoint_as_resource(resource_uri)

    def _generate_input_schema(
        self, func
    ) -> Optional[Dict[str, Union[str, Dict, List]]]:
        """Generate JSON schema for function parameters."""
        try:
            sig = inspect.signature(func)
            properties = {}
            required = []

            for param_name, param in sig.parameters.items():
                if param_name in ("self", "cls"):
                    continue

                param_type = param.annotation
                if param_type == inspect.Parameter.empty:
                    param_type = str

                # Basic type mapping - this should be enhanced
                type_map = {
                    str: {"type": "string"},
                    int: {"type": "integer"},
                    float: {"type": "number"},
                    bool: {"type": "boolean"},
                    list: {"type": "array"},
                    dict: {"type": "object"},
                }

                properties[param_name] = type_map.get(param_type, {"type": "string"})

                if param.default == inspect.Parameter.empty:
                    required.append(param_name)

            schema = (
                {"type": "object", "properties": properties, "required": required}
                if properties
                else None
            )

            return schema

        except Exception:
            return None

    async def _call_endpoint(
        self,
        tool_name: str,
        kwargs: Dict[str, Union[str, int, float, bool, List, Dict]],
    ) -> Union[str, int, float, bool, List, Dict]:
        """Call a lihil endpoint from MCP tool."""
        if tool_name not in self._endpoint_map:
            raise MCPError(f"Tool {tool_name} not found")

        route, endpoint = self._endpoint_map[tool_name]
        func = endpoint.unwrapped_func

        try:
            # Get function signature and validate arguments
            sig = inspect.signature(func)
            bound_args = sig.bind(**kwargs)
            bound_args.apply_defaults()

            # Call the function
            if inspect.iscoroutinefunction(func):
                result = await func(**bound_args.arguments)
            else:
                result = func(**bound_args.arguments)

            # Ensure result is JSON serializable
            if isinstance(result, (dict, list, str, int, float, bool, type(None))):
                return result
            else:
                return json.loads(json.dumps(result, default=str))

        except Exception as e:
            raise MCPError(f"Error calling endpoint {tool_name}: {e}")

    async def _call_endpoint_as_resource(
        self, uri: str
    ) -> Union[str, int, float, bool, List, Dict]:
        """Call a lihil endpoint from MCP resource."""
        if uri not in self._endpoint_map:
            raise MCPError(f"Resource {uri} not found")

        route, endpoint = self._endpoint_map[uri]
        func = endpoint.unwrapped_func

        try:
            # Call the function (resources typically don't take parameters)
            if inspect.iscoroutinefunction(func):
                result = await func()
            else:
                result = func()

            # Ensure result is JSON serializable
            if isinstance(result, (dict, list, str, int, float, bool, type(None))):
                return result
            else:
                return json.loads(json.dumps(result, default=str))

        except Exception as e:
            raise MCPError(f"Error accessing resource {uri}: {e}")

    @property
    def tools(self) -> Dict[str, MCPToolInfo]:
        """Get registered MCP tools."""
        return self._tools.copy()

    @property
    def resources(self) -> Dict[str, MCPResourceInfo]:
        """Get registered MCP resources."""
        return self._resources.copy()

    async def handle_mcp_request(
        self, scope: Dict[str, Union[str, int, List, Dict]], receive, send
    ) -> None:
        """Handle MCP protocol requests."""
        # This will be implemented in the transport layer
        pass
