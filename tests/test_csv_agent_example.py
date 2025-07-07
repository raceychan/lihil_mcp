"""Tests for the CSV Agent example structure to ensure it works properly."""

import sys
import os
import pytest

def test_csv_agent_import_structure():
    """Test that the CSV agent can be imported and has the right structure."""
    # This test verifies the example structure without requiring pandas
    try:
        # Add the examples directory to the path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'examples', 'csv_agent'))
        
        # Check if pandas is available
        try:
            import pandas as pd
            import numpy as np
            pandas_available = True
        except ImportError:
            pandas_available = False
        
        if pandas_available:
            from csv_agent import create_csv_agent_app
            from lihil_mcp import LihilMCP
            
            # Test that the app can be created
            app, mcp_config = create_csv_agent_app()
            assert app is not None
            assert mcp_config is not None
            assert mcp_config.server_name == "csv-ai-agent"
            assert mcp_config.enabled is True
            assert mcp_config.auto_expose is False
            
            # Test MCP integration
            lihil_mcp = LihilMCP(app, mcp_config)
            lihil_mcp.setup_mcp_tools_and_resources()
            
            # Check that tools are registered
            tools = lihil_mcp.tools
            expected_tools = {
                "load_csv", "unload_csv", "get_sample_data", "query_data", 
                "clean_data", "export_csv", "get_statistics"
            }
            assert expected_tools.issubset(set(tools.keys()))
            
            # Check that resources are registered
            resources = lihil_mcp.resources
            expected_resources = {
                "lihil://csv/loaded_files", "lihil://health"
            }
            assert expected_resources.issubset(set(resources.keys()))
            
            print("CSV Agent example structure verified successfully!")
        else:
            print("Pandas not available - skipping CSV agent tests")
            pytest.skip("Pandas not available for CSV agent testing")
            
    except Exception as e:
        pytest.fail(f"Failed to import or test CSV agent structure: {e}")


def test_csv_agent_run_script_structure():
    """Test that the run_agent.py script has the right structure."""
    run_agent_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'csv_agent', 'run_agent.py')
    assert os.path.exists(run_agent_path), "run_agent.py should exist"
    
    with open(run_agent_path, 'r') as f:
        content = f.read()
    
    # Check for key components
    assert "create_csv_agent_app" in content
    assert "LihilMCP" in content
    assert "get_asgi_app" in content
    assert "setup_mcp_tools_and_resources" in content
    assert "uvicorn.run" in content
    print("run_agent.py structure verified successfully!")

