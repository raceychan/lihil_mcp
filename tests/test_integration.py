"""Integration tests using real Lihil app instance and Starlette TestClient."""

import json
import pytest
from starlette.testclient import TestClient

from lihil import Lihil
from lihil.routing import Route
from lihil_mcp.server import LihilMCP
from lihil_mcp.config import MCPConfig
from lihil_mcp.decorators import mcp_tool, mcp_resource


def create_real_lihil_app() -> Lihil:
    """Create a real Lihil application with endpoints that have MCP decorators."""
    
    # Create different routes for different endpoints
    api_route = Route("/api")
    
    @api_route.get
    def get_users():
        """Get all users from the system."""
        return {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
    
    @api_route.post
    @mcp_tool(description="Create a new user")
    def create_user(name: str, email: str = "default@example.com"):
        """Create a new user with name and optional email."""
        return {"id": 3, "name": name, "email": email, "created": True}
    
    # Health endpoint
    health_route = Route("/health")
    
    @health_route.get
    @mcp_resource(uri_template="lihil://health", description="System health status")
    def health_check():
        """Check system health status."""
        return {"status": "healthy", "timestamp": "2023-01-01T00:00:00Z"}
    
    # User management endpoint
    user_mgmt_route = Route("/users")
    
    @user_mgmt_route.put
    @mcp_tool(description="Update user by ID")
    def update_user(user_id: int, name: str = None, email: str = None):
        """Update user information by ID."""
        updates = {}
        if name:
            updates["name"] = name
        if email:
            updates["email"] = email
        return {"id": user_id, "updated": updates, "success": True}
    
    @user_mgmt_route.delete
    def delete_user(user_id: int):
        """Delete user by ID."""
        return {"id": user_id, "deleted": True}
    
    # Admin endpoints
    admin_route = Route("/admin")
    
    @admin_route.get
    def get_stats():
        """Get system statistics."""
        return {"total_users": 10, "active_sessions": 5}
    
    @admin_route.post
    def create_backup(backup_type: str = "full"):
        """Create system backup."""
        return {"backup_id": "backup_123", "type": backup_type, "status": "started"}
    
    # Create the Lihil app with all routes
    app = Lihil(api_route, health_route, user_mgmt_route, admin_route)
    return app


@pytest.fixture
def lihil_app():
    """Create real Lihil application."""
    return create_real_lihil_app()


@pytest.fixture
def mcp_config():
    """Create MCP config for testing."""
    return MCPConfig(server_name="test-mcp-server", auto_expose=False)


@pytest.fixture
def auto_expose_config():
    """Create MCP config with auto-expose enabled."""
    return MCPConfig(server_name="test-mcp-server", auto_expose=True)


@pytest.fixture
def lihil_mcp(lihil_app, mcp_config):
    """Create LihilMCP instance with real Lihil app."""
    return LihilMCP(lihil_app, mcp_config)


@pytest.fixture
def auto_expose_lihil_mcp(lihil_app, auto_expose_config):
    """Create LihilMCP instance with auto-expose enabled."""
    return LihilMCP(lihil_app, auto_expose_config)


@pytest.fixture
def test_client(lihil_app):
    """Create Starlette TestClient for the real Lihil app with proper lifespan handling."""
    # TestClient automatically handles lifespan events, but we need to ensure it's configured properly
    with TestClient(lihil_app) as client:
        yield client


class TestLihilHTTPIntegration:
    """Integration tests for Lihil app HTTP endpoints using Starlette TestClient."""
    
    def test_get_users_endpoint(self, test_client):
        """Test GET /api endpoint returns users."""
        response = test_client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) == 2
        assert data["users"][0]["name"] == "Alice"
    
    def test_create_user_endpoint(self, test_client):
        """Test POST /api endpoint creates user."""
        user_data = {"name": "Charlie", "email": "charlie@example.com"}
        response = test_client.post("/api", params=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Charlie"
        assert data["email"] == "charlie@example.com"
        assert data["created"] is True
    
    def test_health_check_endpoint(self, test_client):
        """Test GET /health endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_update_user_endpoint(self, test_client):
        """Test PUT /users endpoint."""
        update_data = {"user_id": 1, "name": "Alice Updated", "email": "alice.new@example.com"}
        response = test_client.put("/users", params=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["updated"]["name"] == "Alice Updated"
        assert data["success"] is True
    
    def test_delete_user_endpoint(self, test_client):
        """Test DELETE /users endpoint."""
        response = test_client.request("DELETE", "/users", params={"user_id": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["deleted"] is True
    
    def test_admin_stats_endpoint(self, test_client):
        """Test GET /admin endpoint."""
        response = test_client.get("/admin")
        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] == 10
        assert data["active_sessions"] == 5
    
    def test_admin_backup_endpoint(self, test_client):
        """Test POST /admin endpoint."""
        backup_data = {"backup_type": "incremental"}
        response = test_client.post("/admin", params=backup_data)
        assert response.status_code == 200
        data = response.json()
        assert data["backup_id"] == "backup_123"
        assert data["type"] == "incremental"
        assert data["status"] == "started"


class TestLihilMCPIntegration:
    """Integration tests for MCP server with real Lihil app."""
    
    def test_mcp_tools_registration_from_lihil_endpoints(self, lihil_mcp):
        """Test that MCP tools are properly registered from decorated Lihil endpoints."""
        tools = lihil_mcp.tools
        
        # Check that decorated tools are registered
        assert "create_user" in tools
        assert "update_user" in tools
        
        # Verify tool metadata comes from the actual functions
        create_user_tool = tools["create_user"]
        assert "Create a new user" in create_user_tool.description
        assert create_user_tool.inputSchema is not None
        assert "name" in create_user_tool.inputSchema["properties"]
        assert "email" in create_user_tool.inputSchema["properties"]
        
        # Verify schema reflects actual function signature
        assert "name" in create_user_tool.inputSchema["required"]  # no default
        assert "email" not in create_user_tool.inputSchema["required"]  # has default
    
    def test_mcp_resources_registration_from_lihil_endpoints(self, lihil_mcp):
        """Test that MCP resources are properly registered from decorated Lihil endpoints."""
        resources = lihil_mcp.resources
        
        # Check that decorated resource is registered
        assert "lihil://health" in resources
        
        # Verify resource metadata comes from the actual function
        health_resource = resources["lihil://health"]
        assert "System health status" in health_resource.description
        assert health_resource.mimeType == "application/json"
    
    def test_auto_expose_integration(self, auto_expose_lihil_mcp):
        """Test auto-exposure of Lihil endpoints as MCP tools/resources."""
        tools = auto_expose_lihil_mcp.tools
        resources = auto_expose_lihil_mcp.resources
        
        # POST endpoints should be auto-registered as tools  
        assert "create_backup" in tools
        
        # GET endpoints should be auto-registered as resources
        # Check for resources that match our GET endpoints
        resource_uris = list(resources.keys())
        assert any("admin" in uri for uri in resource_uris)  # /admin GET endpoint
    
    @pytest.mark.asyncio
    async def test_mcp_tool_execution_calls_lihil_functions(self, lihil_mcp):
        """Test that executing MCP tools actually calls the Lihil endpoint functions."""
        # Test create_user tool - this should call the actual function
        result = await lihil_mcp._call_endpoint("create_user", {
            "name": "John",
            "email": "john@example.com"
        })
        
        # Verify the result comes from the actual function
        assert result["name"] == "John"
        assert result["email"] == "john@example.com"
        assert result["created"] is True
        assert result["id"] == 3  # This specific value comes from our function
    
    @pytest.mark.asyncio
    async def test_mcp_tool_execution_with_defaults(self, lihil_mcp):
        """Test MCP tool execution respects function defaults."""
        # Test create_user tool with default email
        result = await lihil_mcp._call_endpoint("create_user", {
            "name": "Jane"
        })
        
        # Should use the default email from the function
        assert result["name"] == "Jane"
        assert result["email"] == "default@example.com"
        assert result["created"] is True
    
    @pytest.mark.asyncio
    async def test_mcp_tool_with_typed_parameters(self, lihil_mcp):
        """Test MCP tool execution with typed parameters."""
        # Test update_user tool with integer user_id
        result = await lihil_mcp._call_endpoint("update_user", {
            "user_id": 42,
            "name": "Updated Name"
        })
        
        # Verify the function received the correct types
        assert result["id"] == 42
        assert result["updated"]["name"] == "Updated Name"
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_mcp_resource_access_calls_lihil_functions(self, lihil_mcp):
        """Test that accessing MCP resources calls the actual Lihil endpoint functions."""
        # Test health resource - this should call the actual function
        result = await lihil_mcp._call_endpoint_as_resource("lihil://health")
        
        # Verify the result comes from the actual function
        assert result["status"] == "healthy"
        assert result["timestamp"] == "2023-01-01T00:00:00Z"  # Specific value from our function
    
    def test_input_schema_generation_from_lihil_functions(self, lihil_mcp):
        """Test that input schemas are correctly generated from actual Lihil function signatures."""
        tools = lihil_mcp.tools
        
        # Check create_user tool schema matches the actual function signature
        create_user_tool = tools["create_user"]
        schema = create_user_tool.inputSchema
        
        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "email" in schema["properties"]
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["email"]["type"] == "string"
        
        # Verify required fields match function signature (no defaults = required)
        assert "name" in schema["required"]
        assert "email" not in schema["required"]
        
        # Check update_user tool schema
        update_user_tool = tools["update_user"]
        update_schema = update_user_tool.inputSchema
        
        assert "user_id" in update_schema["properties"]
        assert update_schema["properties"]["user_id"]["type"] == "integer"
        assert "user_id" in update_schema["required"]  # no default value


class TestEndToEndIntegration:
    """End-to-end integration tests combining HTTP and MCP access to the same Lihil functions."""
    
    def test_same_function_accessible_via_http_and_mcp(self, test_client, lihil_mcp):
        """Test that the same Lihil function can be called via both HTTP and MCP."""
        # Test via HTTP
        http_response = test_client.post("/api", params={
            "name": "HTTP User",
            "email": "http@example.com"
        })
        assert http_response.status_code == 200
        http_data = http_response.json()
        
        # Test via MCP - this should call the same underlying function
        import asyncio
        mcp_result = asyncio.run(lihil_mcp._call_endpoint("create_user", {
            "name": "MCP User", 
            "email": "mcp@example.com"
        }))
        
        # Both should have same structure (same function), different data
        assert http_data["created"] == mcp_result["created"]
        assert http_data["id"] == mcp_result["id"]
        assert http_data["name"] != mcp_result["name"]  # Different input data
        assert http_data["email"] != mcp_result["email"]  # Different input data
    
    def test_mcp_only_functionality(self, lihil_mcp):
        """Test MCP-specific functionality that works regardless of HTTP issues."""
        # Test via MCP - this calls the same underlying function that would be used for HTTP
        import asyncio
        mcp_result1 = asyncio.run(lihil_mcp._call_endpoint("create_user", {
            "name": "MCP User 1", 
            "email": "mcp1@example.com"
        }))
        
        mcp_result2 = asyncio.run(lihil_mcp._call_endpoint("create_user", {
            "name": "MCP User 2", 
            "email": "mcp2@example.com"
        }))
        
        # Both should have same structure (same function), different data
        assert mcp_result1["created"] == mcp_result2["created"]
        assert mcp_result1["id"] == mcp_result2["id"]  # Both use the same function logic
        assert mcp_result1["name"] != mcp_result2["name"]  # Different input data
        assert mcp_result1["email"] != mcp_result2["email"]  # Different input data
    
    @pytest.mark.asyncio
    async def test_mcp_error_handling_with_real_functions(self, lihil_mcp):
        """Test MCP error handling when calling real Lihil functions."""
        from lihil_mcp.types import MCPError
        
        # Test calling non-existent tool
        with pytest.raises(MCPError, match="Tool nonexistent not found"):
            await lihil_mcp._call_endpoint("nonexistent", {})
        
        # Test calling tool with missing required arguments
        with pytest.raises(MCPError):
            await lihil_mcp._call_endpoint("create_user", {})  # missing required 'name'
    
    def test_lihil_app_structure_integration(self, lihil_app, lihil_mcp):
        """Test that the MCP plugin correctly integrates with Lihil's app structure."""
        # Verify the MCP plugin found all the routes from the Lihil app
        assert lihil_mcp.app == lihil_app
        assert hasattr(lihil_mcp.app, 'routes')
        assert len(lihil_mcp.app.routes) == 4  # api, health, users, admin routes
        
        # Verify endpoint mapping was created
        assert len(lihil_mcp._endpoint_map) > 0
        
        # Verify both tools and resources were registered
        tools = lihil_mcp.tools
        resources = lihil_mcp.resources
        assert len(tools) >= 2  # create_user, update_user
        assert len(resources) >= 1  # health_check