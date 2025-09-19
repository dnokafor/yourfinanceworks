# FastMCP Refactoring Changes

## Latest Changes (2024-12-19)

### AI-Powered Intent Classification for MCP Integration

#### 🤖 AI-Based Intent Classification System
- **✅ Eliminated Hardcoded Patterns**: Replaced keyword pattern matching with AI-based intent classification
- **✅ Dynamic Tool Selection**: AI automatically determines which MCP tool to use based on message meaning
- **✅ Natural Language Understanding**: Supports natural language variations without maintaining pattern lists
- **✅ Improved Accuracy**: AI classification provides better understanding of user intent
- **✅ Automatic Default Config**: System automatically sets single active AI config as default
- **✅ Enhanced Debugging**: Added comprehensive logging for intent classification and tool selection

#### 🔧 Technical Implementation
  - **AI Intent Classification**: Uses AI to classify user messages into business categories (analyze_patterns, payments, clients, invoices, expenses, statements, currencies, outstanding, overdue, statistics, general)
- **Dynamic MCP Tool Routing**: Based on AI classification, automatically routes to appropriate MCP tools
- **Fallback to LLM**: General queries not related to business data use configured LLM
- **Request Format Fix**: Fixed 422 error by updating AI chat endpoint to accept JSON request body

#### 📝 Usage Examples
```
# These all get classified as "statements" intent:
"Show bank statements"
"What statements do I have?"
"Display my banking information"
"List all my bank account statements"

# These all get classified as "expenses" intent:
"List all expenses"
"What did I spend money on?"
"Show my business expenses"
"Display expense information"
```

## Latest Code Quality & Performance Updates

### Performance Optimizations (Current Session)
- **`api_client.py`**: Fixed performance inefficiencies in search methods
  - Implemented batch processing for `search_clients` and `search_invoices`
  - Added early termination when sufficient results found
  - Reduced memory usage with 100-item batch processing
  - Optimized field access with individual checks instead of array creation

### Security Fixes (Current Session)
- **`auth_client.py`**: Fixed CWE-396,397 generic exception handling
  - Replaced generic `Exception` with specific types: `FileNotFoundError`, `json.JSONDecodeError`, `KeyError`, `ValueError`
  - Follows security best practices for exception handling

### Import Optimizations (Current Session)
- **`api_client.py`**: Improved import efficiency
  - Changed from `import httpx` to `from httpx import AsyncClient, HTTPStatusError`
  - Enhanced performance, clarity, and maintainability

### Code Maintainability (Current Session)
- **`tools.py`**: Refactored complex date parsing logic
  - Extracted repetitive date parsing into `_parse_date_filter` helper method
  - Reduced code duplication in `query_payments` method
  - Improved readability and maintainability

## New Tools Added (Latest Update)

The MCP server has been expanded with comprehensive new tools to support the full invoice application functionality:

### Currency Management Tools
- **`list_currencies`**: List supported currencies with optional filtering for active currencies
- **`create_currency`**: Create custom currencies for the tenant (e.g., Bitcoin, custom tokens)
- **`convert_currency`**: Convert amounts between currencies using exchange rates

### Payment Management Tools
- **`list_payments`**: List all payments with pagination support
- **`create_payment`**: Record payments for invoices with various payment methods

### Settings & Configuration Tools
- **`get_settings`**: Retrieve tenant settings and company information
- **`get_tenant_info`**: Get current tenant details and configuration

### Discount Rules Tools
- **`list_discount_rules`**: List all discount rules for the tenant
- **`create_discount_rule`**: Create new discount rules with percentage or fixed amounts

### CRM Tools
- **`create_client_note`**: Create notes for client interactions and follow-ups

### Email Integration Tools
- **`send_invoice_email`**: Send invoices via email with customizable messages
- **`test_email_configuration`**: Test email setup and configuration

### Expense Management Tools
- **`list_expenses`**: List all expenses with filtering and pagination
- **`get_expense`**: Get detailed expense information by ID
- **`create_expense`**: Create new business expenses with tax calculations
- **`update_expense`**: Update existing expense details
- **`delete_expense`**: Remove expenses from the system
- **`upload_expense_receipt`**: Upload receipt attachments (PDF, JPG, PNG)
- **`list_expense_attachments`**: List all attachments for an expense
- **`delete_expense_attachment`**: Remove specific expense attachments

### Statement Management Tools
- **`list_statements`**: List all imported statements
- **`get_bank_statement`**: Get detailed bank statement information
- **`reprocess_bank_statement`**: Reprocess bank statement for transaction matching
- **`update_bank_statement_meta`**: Update bank statement metadata
- **`delete_bank_statement`**: Remove bank statements from the system

### Example Usage of New Tools

```bash
# Currency Management
python -m MCP --email user@example.com --password password
# Then use tools like:
# - "List all active currencies"
# - "Create a Bitcoin currency with symbol ₿"
# - "Convert 100 USD to EUR"

# Payment Management
# - "Record a payment of $500 for invoice #123"
# - "List all payments from last month"

# Expense Management
# - "List all expenses from this quarter"
# - "Create an expense for office supplies costing $150"
# - "Upload a receipt for expense #456"
# - "Show me unlinked expenses"
# - "Update expense #789 with new category"

# Statement Management
# - "List all imported bank statements"
# - "Get details for bank statement #123"
# - "Reprocess bank statement for better matching"
# - "Delete old bank statement #456"

# Settings & Configuration
# - "Get my company settings"
# - "Show tenant information"

# Discount Rules
# - "Create a 10% discount for orders over $1000"
# - "List all discount rules"

# CRM
# - "Add a note to client John Doe about our meeting"

# Email
# - "Send invoice #123 via email"
# - "Test my email configuration"
```

### Updated Available Tools List

The complete list of available tools now includes:

**Client Management:**
- `list_clients`, `search_clients`, `get_client`, `create_client`

**Invoice Management:**
- `list_invoices`, `search_invoices`, `get_invoice`, `create_invoice`

**Expense Management:**
- `list_expenses`, `get_expense`, `create_expense`, `update_expense`, `delete_expense`
- `upload_expense_receipt`, `list_expense_attachments`, `delete_expense_attachment`

**Statement Management:**
- `list_statements`, `get_bank_statement`, `reprocess_bank_statement`
- `update_bank_statement_meta`, `delete_bank_statement`

**Analytics:**
- `get_clients_with_outstanding_balance`, `get_overdue_invoices`, `get_invoice_stats`

**Currency Management:**
- `list_currencies`, `create_currency`, `convert_currency`

**Payment Management:**
- `list_payments`, `create_payment`

**Settings & Configuration:**
- `get_settings`, `get_tenant_info`

**Discount Rules:**
- `list_discount_rules`, `create_discount_rule`

**CRM:**
- `create_client_note`

**Email Integration:**
- `send_invoice_email`, `test_email_configuration`

## Overview

The Invoice Application MCP server has been refactored to use **FastMCP**, a modern and simplified framework for building Model Context Protocol servers.

## Key Changes

### 1. Dependencies (`requirements.txt`)
- **Before**: `mcp>=1.0.0`
- **After**: `fastmcp>=0.2.0`

### 2. Server Implementation (`server.py`)

**Before (Traditional MCP)**:
```python
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import CallToolRequest, CallToolResult, ListToolsRequest, ListToolsResult, TextContent

class InvoiceMCPServer:
    def __init__(self):
        self.server = Server("invoice-app-mcp")
        self._register_handlers()
    
    def _register_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            return ListToolsResult(tools=TOOLS)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            # Complex request handling logic...
```

**After (FastMCP)**:
```python
from fastmcp import FastMCP

mcp = FastMCP("Invoice Application MCP Server")

@mcp.tool()
async def list_clients(skip: int = 0, limit: int = 100) -> dict:
    """List all clients with pagination support."""
    if tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await tools.list_clients(skip=skip, limit=limit)
```

### 3. Tool Definitions (`tools.py`)

**Before (Traditional MCP)**:
```python
from mcp.types import Tool, TextContent

TOOLS: List[Tool] = [
    Tool(
        name="list_clients",
        description="List all clients with pagination support.",
        inputSchema=ListClientsArgs.model_json_schema()
    ),
    # ... more tools
]

class InvoiceTools:
    async def list_clients(self, arguments: Dict[str, Any]) -> List[TextContent]:
        args = ListClientsArgs(**arguments)
        clients = await self.api_client.list_clients(skip=args.skip, limit=args.limit)
        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2, default=str)
        )]
```

**After (FastMCP)**:
```python
class InvoiceTools:
    async def list_clients(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        clients = await self.api_client.list_clients(skip=skip, limit=limit)
        return {
            "success": True,
            "data": clients,
            "count": len(clients),
            "pagination": {"skip": skip, "limit": limit}
        }
```

## Benefits Achieved

### 1. **Reduced Code Complexity**
- **Lines of code**: Reduced from ~430 lines to ~260 lines (40% reduction)
- **Boilerplate elimination**: No more manual tool schema definitions
- **Simpler request handling**: Direct function calls instead of complex routing

### 2. **Improved Developer Experience**
- **Type Safety**: Full type hint support with automatic schema generation
- **Decorator Pattern**: Clean `@mcp.tool()` decorators instead of complex class methods
- **Direct Returns**: Return Python dictionaries instead of TextContent objects

### 3. **Better Maintainability**
- **Less Error-Prone**: Fewer places where bugs can occur
- **Easier Testing**: Simple function calls instead of complex request objects
- **Clear Separation**: Tools vs. server logic clearly separated

### 4. **Modern Python Features**
- **Async/Await**: Native support throughout
- **Type Hints**: Used for automatic schema generation
- **Optional Parameters**: Natural Python syntax

## Migration Path

If you have existing traditional MCP code, here's how to migrate:

1. **Update Dependencies**:
   ```bash
   pip uninstall mcp
   pip install fastmcp
   ```

2. **Refactor Server**:
   - Replace `Server` class with `FastMCP` instance
   - Convert tool handlers to `@mcp.tool()` decorated functions
   - Use type hints for parameter definitions

3. **Simplify Tool Methods**:
   - Remove `arguments: Dict[str, Any]` parameter
   - Use direct parameters with type hints
   - Return dictionaries instead of `TextContent` objects

4. **Update Tests**:
   - Test functions directly instead of through MCP protocol
   - Use returned dictionaries instead of parsing JSON from text

## Example Usage

### Starting the Server
```bash
python -m MCP.server --email user@example.com --password password
```

### Available Tools (same as before)
- `list_clients`
- `search_clients`
- `get_client`
- `create_client`
- `list_invoices`
- `search_invoices`
- `get_invoice`
- `create_invoice`
- `get_clients_with_outstanding_balance`
- `get_overdue_invoices`
- `get_invoice_stats`

### Claude Desktop Configuration (unchanged)
```json
{
  "mcpServers": {
    "invoice-app": {
      "command": "python",
      "args": ["-m", "MCP.server", "--email", "user@example.com", "--password", "password"],
      "cwd": "/path/to/invoice/app/api"
    }
  }
}
```

## Conclusion

The FastMCP refactoring maintains all existing functionality while significantly simplifying the codebase and improving developer experience. The API remains the same for end users, but development and maintenance are now much easier.