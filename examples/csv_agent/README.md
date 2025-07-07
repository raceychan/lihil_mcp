# CSV AI Agent Example

This example demonstrates how to create an AI agent that helps with CSV file operations using the Lihil framework with MCP (Model Context Protocol) integration.

## Features

The CSV AI Agent provides the following capabilities:

- **File Management**: Load, list, and unload CSV files from memory
- **Data Querying**: Get sample data, query with filters and conditions
- **Data Analysis**: Statistical summaries, data profiling
- **Data Cleaning**: Handle missing values, remove duplicates
- **Data Export**: Export processed data to new files
- **MCP Integration**: All operations exposed as MCP tools and resources

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Or install individually:
```bash
pip install lihil-mcp pandas numpy uvicorn
```

## Usage

### Starting the Agent

```bash
python csv_agent.py
```

The agent will start on `http://localhost:8000` with MCP integration enabled.

### Available Endpoints

#### CSV Management
- `POST /csv` - Load a CSV file into memory
- `GET /csv` - List all loaded CSV files
- `DELETE /csv` - Remove a CSV file from memory

#### Data Operations
- `GET /data` - Get sample rows from a loaded CSV
- `POST /data` - Query CSV data with filters

#### Analysis & Cleaning
- `GET /analysis/{filename}/stats` - Get statistical summary
- `POST /analysis` - Clean data (handle missing values, duplicates)
- `POST /analysis` - Export processed data

#### Health Check
- `GET /health` - Check agent health status

## MCP Integration

All endpoints are exposed as MCP tools and resources:

### MCP Tools (POST endpoints)
- `load_csv` - Load CSV files
- `unload_csv` - Remove files from memory
- `query_data` - Query data with filters
- `clean_data` - Clean and process data
- `export_csv` - Export processed data

### MCP Resources (GET endpoints)
- `csv://loaded_files` - List of loaded files
- `analysis://{filename}/stats` - Statistical summaries
- `csv_agent://health` - Health status

## Example Usage

### 1. Load Sample Data

```python
# Load the sample employee data
response = requests.post("http://localhost:8000/csv", 
    params={
        "filepath": "sample_data/employees.csv",
        "delimiter": ",",
        "encoding": "utf-8"
    }
)
```

### 2. Query Data

```python
# Query employees in Engineering department
response = requests.post("http://localhost:8000/data",
    params={
        "filename": "employees.csv",
        "column": "department",
        "value": "Engineering",
        "condition": "equals",
        "limit": 10
    }
)
```

### 3. Get Statistics

```python
# Get statistical summary
response = requests.get("http://localhost:8000/analysis/employees.csv/stats")
```

### 4. Clean Data

```python
# Clean messy data
response = requests.post("http://localhost:8000/analysis",
    params={
        "filename": "messy_data.csv",
        "drop_duplicates": True,
        "fill_na_method": "fill_value",
        "fill_na_value": "Unknown"
    }
)
```

## Sample Data

The example includes three sample CSV files:

1. **employees.csv** - Clean employee data with departments, salaries, etc.
2. **sales_data.csv** - Sales transactions with products, dates, and amounts
3. **messy_data.csv** - Data with missing values and duplicates for testing cleanup

## MCP Client Usage

When using with MCP-compatible clients like Claude Code:

```python
# The agent exposes tools that can be called via MCP
load_csv_tool = mcp_client.get_tool("load_csv")
result = await load_csv_tool.call({
    "filepath": "sample_data/employees.csv"
})

query_tool = mcp_client.get_tool("query_data")
engineering_employees = await query_tool.call({
    "filename": "employees.csv",
    "column": "department",
    "value": "Engineering",
    "condition": "equals"
})
```

## Architecture

The agent is built using:

- **Lihil Framework**: Modern Python web framework with dependency injection
- **MCP Integration**: Exposes endpoints as MCP tools and resources
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Uvicorn**: ASGI server for production deployment

## Key Features

### Memory Management
- Files are loaded into memory for fast access
- Automatic memory usage reporting
- Ability to unload files to free memory

### Data Processing
- Support for various delimiters and encodings
- Flexible querying with multiple condition types
- Statistical analysis for both numeric and categorical data

### Data Cleaning
- Multiple strategies for handling missing values
- Duplicate detection and removal
- Data type inference and conversion

### Export Options
- Multiple output formats
- Configurable delimiters
- Index inclusion options

## Error Handling

The agent includes comprehensive error handling:

- File not found errors
- Invalid query parameters
- Data type conversion errors
- Memory management errors

All errors are returned in a consistent JSON format with descriptive messages.

## Extension Points

The agent can be extended with:

- Additional data cleaning algorithms
- More sophisticated query capabilities
- Integration with other data sources
- Custom export formats
- Machine learning model integration

## Production Considerations

For production use:

1. Add authentication and authorization
2. Implement rate limiting
3. Add logging and monitoring
4. Configure proper error handling
5. Set up data persistence
6. Add input validation and sanitization