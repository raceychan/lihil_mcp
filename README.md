# Lihil MCP

MCP (Model Context Protocol) integration for the [Lihil](https://github.com/raceychan/lihil) framework.

This package enables Lihil applications to expose their endpoints as MCP tools and resources, allowing them to be used by MCP-compatible clients like Claude Code.

## Installation

```bash
pip install lihil-mcp
```

Or with uv:

```bash
uv add lihil-mcp
```

## Quick Start

### Basic Usage

```python
from lihil import Lihil
from lihil_mcp import MCPConfig

# Create your Lihil app
app = Lihil()

# Enable MCP with auto-exposure
mcp_config = MCPConfig(enabled=True, auto_expose=True)
app.enable_mcp(mcp_config)

# Your endpoints are automatically exposed as MCP tools/resources
@app.get("/users/{user_id}")
async def get_user(user_id: int) -> dict:
    return {"id": user_id, "name": "User"}

@app.post("/send-email")
async def send_email(to: str, subject: str, body: str) -> str:
    return f"Email sent to {to}"
```

### Manual MCP Decoration

```python
from lihil import Lihil
from lihil_mcp import MCPConfig, mcp_tool, mcp_resource

app = Lihil()
mcp_config = MCPConfig(enabled=True, auto_expose=False)
app.enable_mcp(mcp_config)

# Explicitly mark endpoints as MCP tools
@app.post("/send-email")
@mcp_tool(title="Send Email", description="Send an email to a recipient")
async def send_email(to: str, subject: str, body: str) -> str:
    # Email sending logic
    return f"Email sent to {to}"

# Explicitly mark endpoints as MCP resources
@app.get("/users/{user_id}")
@mcp_resource("users://{user_id}", title="User Profile", description="Get user profile")
async def get_user(user_id: int) -> dict:
    return {"id": user_id, "name": "User"}
```

## Configuration

### MCPConfig Options

```python
from lihil_mcp import MCPConfig

config = MCPConfig(
    enabled=True,                    # Enable MCP functionality
    server_name="my-api-server",     # Name of the MCP server
    auto_expose=True,                # Auto-expose all endpoints as MCP tools/resources
    expose_docs=True,                # Expose OpenAPI docs as MCP resources
    auth_required=False,             # Whether authentication is required
    transport="asgi",                # Transport protocol ("asgi" or "stdio")
    mcp_path_prefix="/mcp"          # URL path prefix for MCP endpoints
)
```

## How It Works

### Auto-Exposure Mode

When `auto_expose=True`:
- **GET endpoints** - Exposed as MCP resources
- **POST/PUT/PATCH endpoints** - Exposed as MCP tools

### Manual Decoration

Use decorators for fine-grained control:
- `@mcp_tool()` - Mark endpoint as MCP tool
- `@mcp_resource()` - Mark endpoint as MCP resource

### Transport

The package uses ASGI transport to handle both regular HTTP requests and MCP protocol requests on the same server.

## Integration with Lihil Features

### Authentication

Leverage Lihil's auth plugins:

```python
from lihil_mcp import MCPConfig

# Enable authentication for MCP operations
config = MCPConfig(enabled=True, auth_required=True)
```

### Dependency Injection

MCP works seamlessly with Lihil's dependency injection system:

```python
from lihil import Lihil, Provide
from lihil_mcp import mcp_tool

app = Lihil()

class EmailService:
    def send(self, to: str, subject: str, body: str) -> str:
        return f"Email sent to {to}"

@app.post("/send-email")
@mcp_tool(title="Send Email")
async def send_email(
    to: str, 
    subject: str, 
    body: str,
    email_service: EmailService = Provide()
) -> str:
    return email_service.send(to, subject, body)
```

## Examples

See the [examples directory](./examples) for complete working examples.

## Requirements

- Python 3.10+
- lihil >= 0.2.0
- mcp >= 1.8.1

## Development

```bash
# Clone the repository
git clone https://github.com/raceychan/lihil-mcp.git
cd lihil-mcp

# Install with development dependencies
uv sync --group dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=lihil_mcp
```

## License

MIT License - see [LICENSE](./LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.