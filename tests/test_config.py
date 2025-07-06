import pytest
from lihil_mcp.config import MCPConfig


def test_mcp_config_default():
    config = MCPConfig()
    assert config.server_name == "lihil-mcp-server"
    assert config.auto_expose is True


def test_mcp_config_custom():
    config = MCPConfig(
        server_name="custom-server",
        auto_expose=True
    )
    assert config.server_name == "custom-server"
    assert config.auto_expose is True