"""
CSV AI Agent using Lihil-MCP

This example demonstrates how to create an AI agent that helps with CSV file operations
using the Lihil framework with MCP (Model Context Protocol) integration.

The agent provides the following capabilities:
- Load and analyze CSV files
- Get basic statistics and information
- Query data with filters
- Export processed data
- Data cleaning operations
"""

import os
import io
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

import pandas as pd
import numpy as np
from lihil import Lihil
from lihil.routing import Route
from lihil_mcp import MCPConfig, mcp_tool, mcp_resource

# Global store for loaded CSV files
csv_store: Dict[str, pd.DataFrame] = {}

@dataclass
class CSVInfo:
    filename: str
    rows: int
    columns: int
    column_names: List[str]
    dtypes: Dict[str, str]
    memory_usage: str

def create_csv_agent_app() -> tuple[Lihil, MCPConfig]:
    """Create the CSV Agent Lihil application with MCP integration."""
    
    # Create routes
    csv_route = Route("/csv")
    data_route = Route("/data")
    analysis_route = Route("/analysis")
    
    # CSV Management Endpoints
    
    @csv_route.post
    @mcp_tool(description="Load a CSV file into memory for analysis")
    def load_csv(filepath: str, delimiter: str = ",", encoding: str = "utf-8") -> Dict[str, Any]:
        """Load a CSV file into memory and return basic information."""
        try:
            if not os.path.exists(filepath):
                return {"error": f"File not found: {filepath}"}
            
            df = pd.read_csv(filepath, delimiter=delimiter, encoding=encoding)
            filename = Path(filepath).name
            csv_store[filename] = df
            
            return {
                "message": f"Successfully loaded {filename}",
                "filename": filename,
                "shape": df.shape,
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
            }
        except Exception as e:
            return {"error": f"Failed to load CSV: {str(e)}"}
    
    @csv_route.get
    @mcp_resource(uri_template="lihil://csv/loaded_files", description="Get list of loaded CSV files")
    def list_loaded_files() -> Dict[str, Any]:
        """Get information about all loaded CSV files."""
        files_info = []
        for filename, df in csv_store.items():
            files_info.append({
                "filename": filename,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
            })
        
        return {
            "loaded_files": files_info,
            "total_files": len(csv_store)
        }
    
    @csv_route.delete
    @mcp_tool(description="Remove a loaded CSV file from memory")
    def unload_csv(filename: str) -> Dict[str, Any]:
        """Remove a CSV file from memory."""
        if filename in csv_store:
            del csv_store[filename]
            return {"message": f"Successfully unloaded {filename}"}
        return {"error": f"File {filename} not found in memory"}
    
    # Data Query Endpoints
    
    @data_route.get
    @mcp_tool(description="Get sample rows from a loaded CSV file")
    def get_sample_data(filename: str, n_rows: int = 5, start_row: int = 0) -> Dict[str, Any]:
        """Get sample rows from a loaded CSV file."""
        if filename not in csv_store:
            return {"error": f"File {filename} not loaded"}
        
        df = csv_store[filename]
        sample_df = df.iloc[start_row:start_row + n_rows]
        
        return {
            "filename": filename,
            "sample_data": sample_df.to_dict(orient="records"),
            "start_row": start_row,
            "rows_returned": len(sample_df),
            "total_rows": len(df)
        }
    
    @data_route.post
    @mcp_tool(description="Query CSV data with filters and conditions")
    def query_data(
        filename: str,
        column: Optional[str] = None,
        value: Optional[str] = None,
        condition: str = "equals",
        limit: int = 100
    ) -> Dict[str, Any]:
        """Query CSV data with filters."""
        if filename not in csv_store:
            return {"error": f"File {filename} not loaded"}
        
        df = csv_store[filename]
        
        if column and value:
            if column not in df.columns:
                return {"error": f"Column {column} not found"}
            
            try:
                if condition == "equals":
                    filtered_df = df[df[column] == value]
                elif condition == "contains":
                    filtered_df = df[df[column].astype(str).str.contains(value, na=False)]
                elif condition == "greater_than":
                    filtered_df = df[df[column] > pd.to_numeric(value)]
                elif condition == "less_than":
                    filtered_df = df[df[column] < pd.to_numeric(value)]
                else:
                    return {"error": f"Unsupported condition: {condition}"}
                
                result_df = filtered_df.head(limit)
                
                return {
                    "filename": filename,
                    "query": f"{column} {condition} {value}",
                    "results": result_df.to_dict(orient="records"),
                    "total_matches": len(filtered_df),
                    "returned_rows": len(result_df)
                }
            except Exception as e:
                return {"error": f"Query failed: {str(e)}"}
        else:
            # Return all data if no filter
            result_df = df.head(limit)
            return {
                "filename": filename,
                "results": result_df.to_dict(orient="records"),
                "total_rows": len(df),
                "returned_rows": len(result_df)
            }
    
    # Analysis Endpoints
    
    @analysis_route.get
    @mcp_tool(description="Get statistical summary of CSV data")
    def get_statistics(filename: str) -> Dict[str, Any]:
        """Get statistical summary of a loaded CSV file."""
        if filename not in csv_store:
            return {"error": f"File {filename} not loaded"}
        
        df = csv_store[filename]
        
        # Basic info
        info = {
            "filename": filename,
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
        
        # Numeric columns statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            info["numeric_statistics"] = df[numeric_cols].describe().to_dict()
        
        # String columns info
        string_cols = df.select_dtypes(include=['object']).columns
        if len(string_cols) > 0:
            string_info = {}
            for col in string_cols:
                string_info[col] = {
                    "unique_values": df[col].nunique(),
                    "most_common": df[col].value_counts().head(3).to_dict(),
                    "null_count": df[col].isnull().sum()
                }
            info["string_statistics"] = string_info
        
        # Missing values
        info["missing_values"] = df.isnull().sum().to_dict()
        
        return info
    
    @analysis_route.post
    @mcp_tool(description="Clean CSV data by handling missing values and duplicates")
    def clean_data(
        filename: str,
        drop_duplicates: bool = False,
        fill_na_method: str = "none",
        fill_na_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clean CSV data by handling missing values and duplicates."""
        if filename not in csv_store:
            return {"error": f"File {filename} not loaded"}
        
        df = csv_store[filename].copy()
        operations = []
        
        # Handle duplicates
        if drop_duplicates:
            initial_rows = len(df)
            df = df.drop_duplicates()
            duplicates_removed = initial_rows - len(df)
            operations.append(f"Removed {duplicates_removed} duplicate rows")
        
        # Handle missing values
        if fill_na_method != "none":
            na_count = df.isnull().sum().sum()
            if na_count > 0:
                if fill_na_method == "drop":
                    df = df.dropna()
                    operations.append(f"Dropped rows with missing values")
                elif fill_na_method == "fill_value" and fill_na_value:
                    df = df.fillna(fill_na_value)
                    operations.append(f"Filled missing values with '{fill_na_value}'")
                elif fill_na_method == "forward_fill":
                    df = df.ffill()
                    operations.append("Forward filled missing values")
                elif fill_na_method == "backward_fill":
                    df = df.bfill()
                    operations.append("Backward filled missing values")
        
        # Save cleaned data
        cleaned_filename = f"{filename}_cleaned"
        csv_store[cleaned_filename] = df
        
        return {
            "message": f"Data cleaned and saved as {cleaned_filename}",
            "original_filename": filename,
            "cleaned_filename": cleaned_filename,
            "operations": operations,
            "new_shape": df.shape,
            "remaining_missing_values": df.isnull().sum().sum()
        }
    
    @analysis_route.put
    @mcp_tool(description="Export processed CSV data to a new file")
    def export_csv(
        filename: str,
        output_path: str,
        include_index: bool = False,
        delimiter: str = ","
    ) -> Dict[str, Any]:
        """Export a loaded CSV file to a new location."""
        if filename not in csv_store:
            return {"error": f"File {filename} not loaded"}
        
        try:
            df = csv_store[filename]
            df.to_csv(output_path, index=include_index, sep=delimiter)
            
            return {
                "message": f"Successfully exported {filename} to {output_path}",
                "filename": filename,
                "output_path": output_path,
                "rows_exported": len(df),
                "columns_exported": len(df.columns)
            }
        except Exception as e:
            return {"error": f"Export failed: {str(e)}"}
    
    # Health check endpoint
    health_route = Route("/health")
    
    @health_route.get
    @mcp_resource(uri_template="lihil://health", description="CSV Agent health status")
    def health_check() -> Dict[str, Any]:
        """Check the health status of the CSV Agent."""
        return {
            "status": "healthy",
            "service": "CSV AI Agent",
            "loaded_files": len(csv_store),
            "available_memory": "unknown"  # Simplified for this example
        }
    
    # Create the Lihil app
    app = Lihil(csv_route, data_route, analysis_route, health_route)
    
    # Enable MCP
    mcp_config = MCPConfig(
        enabled=True,
        server_name="csv-ai-agent",
        auto_expose=False,  # We're using manual decorators for fine control
        expose_docs=True,
        transport="asgi"
    )
    
    # Note: This would be the pattern if lihil had enable_mcp method
    # For now, we'll return the app and config separately
    return app, mcp_config

if __name__ == "__main__":
    app, mcp_config = create_csv_agent_app()
    
    # Start the server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)