"""
Invoice Application FastMCP Server

This is the main FastMCP server for the Invoice Application.
It provides tools for AI models to interact with the invoice system API.
"""
import argparse
import logging
import sys
from contextlib import asynccontextmanager
from typing import Optional, AsyncIterator, List
from datetime import datetime

from fastmcp import FastMCP

from .api_client import InvoiceAPIClient
from .tools import InvoiceTools
from .config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServerContext:
    """Context class to hold server state"""
    def __init__(self):
        self.api_client: Optional[InvoiceAPIClient] = None
        self.tools: Optional[InvoiceTools] = None

# Global context instance
server_context = ServerContext()

@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[None]:
    """FastMCP lifespan context manager for initialization and cleanup"""
    args = parse_arguments()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Validate required credentials
    if not args.email or not args.password:
        logger.error("Email and password are required for API authentication")
        logger.error("Set them via command line arguments or environment variables:")
        logger.error("  INVOICE_API_EMAIL and INVOICE_API_PASSWORD")
        sys.exit(1)
    
    logger.info("Starting Invoice FastMCP Server...")
    logger.info(f"API Base URL: {args.api_url}")
    
    try:
        # Initialize API client and tools
        try:
            server_context.api_client = InvoiceAPIClient(
                base_url=args.api_url,
                email=args.email,
                password=args.password
            )
            server_context.tools = InvoiceTools(server_context.api_client)
            logger.info(f"Initialized API client for {args.api_url}")
        except Exception as e:
            logger.error(f"Failed to initialize API client: {e}")
            raise
        
        yield
        
    finally:
        # Cleanup
        if server_context.api_client:
            await server_context.api_client.close()
            server_context.api_client = None
            logger.info("Cleaned up API client")

# Initialize FastMCP server with lifespan
mcp = FastMCP("Invoice Application MCP Server", lifespan=lifespan)

# Client Management Tools

@mcp.tool()
async def list_clients(skip: int = 0, limit: int = 100) -> dict:
    """
    List all clients with pagination support. Returns client information including balances.
    
    Args:
        skip: Number of clients to skip for pagination (default: 0)
        limit: Maximum number of clients to return (default: 100)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.list_clients(skip=skip, limit=limit)

@mcp.tool()
async def search_clients(query: str, skip: int = 0, limit: int = 100) -> dict:
    """
    Search for clients by name, email, phone, or address. Supports partial matches.
    
    Args:
        query: Search query to find clients
        skip: Number of results to skip for pagination (default: 0)
        limit: Maximum number of results to return (default: 100)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.search_clients(query=query, skip=skip, limit=limit)

@mcp.tool()
async def get_client(client_id: int) -> dict:
    """
    Get detailed information about a specific client by ID, including balance and payment history.
    
    Args:
        client_id: ID of the client to retrieve
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.get_client(client_id=client_id)

@mcp.tool()
async def create_client(name: str, email: Optional[str] = None, phone: Optional[str] = None, address: Optional[str] = None) -> dict:
    """
    Create a new client with the provided information.
    
    Args:
        name: Client's full name
        email: Client's email address (optional)
        phone: Client's phone number (optional)
        address: Client's address (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.create_client(name=name, email=email, phone=phone, address=address)

# Invoice Management Tools

@mcp.tool()
async def list_invoices(skip: int = 0, limit: int = 100) -> dict:
    """
    List all invoices with pagination support. Returns invoice information including client names and payment status.
    
    Args:
        skip: Number of invoices to skip for pagination (default: 0)
        limit: Maximum number of invoices to return (default: 100)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.list_invoices(skip=skip, limit=limit)

@mcp.tool()
async def search_invoices(query: str, skip: int = 0, limit: int = 100) -> dict:
    """
    Search for invoices by number, client name, status, notes, or amount. Supports partial matches.
    
    Args:
        query: Search query to find invoices
        skip: Number of results to skip for pagination (default: 0)
        limit: Maximum number of results to return (default: 100)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.search_invoices(query=query, skip=skip, limit=limit)

@mcp.tool()
async def get_invoice(invoice_id: int) -> dict:
    """
    Get detailed information about a specific invoice by ID, including client information and payment status.
    
    Args:
        invoice_id: ID of the invoice to retrieve
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.get_invoice(invoice_id=invoice_id)

@mcp.tool()
async def create_invoice(client_id: int, amount: float, due_date: str, status: str = "draft", notes: Optional[str] = None) -> dict:
    """
    Create a new invoice for a client with the specified amount and due date.
    
    Args:
        client_id: ID of the client this invoice belongs to
        amount: Total amount of the invoice
        due_date: Due date in ISO format (YYYY-MM-DD)
        status: Status of the invoice (default: "draft")
        notes: Additional notes for the invoice (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.create_invoice(client_id=client_id, amount=amount, due_date=due_date, status=status, notes=notes)

# Analytics Tools

@mcp.tool()
async def get_clients_with_outstanding_balance() -> dict:
    """
    Get all clients that have outstanding balances (unpaid invoices).
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.get_clients_with_outstanding_balance()

@mcp.tool()
async def get_overdue_invoices() -> dict:
    """
    Get all invoices that are past their due date and still unpaid.
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.get_overdue_invoices()

@mcp.tool()
async def get_invoice_stats() -> dict:
    """
    Get overall invoice statistics including total income and other metrics.
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.get_invoice_stats()

@mcp.tool()
async def analyze_invoice_patterns() -> dict:
    """Analyze invoice patterns to identify trends and provide recommendations."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.analyze_invoice_patterns()

@mcp.tool()
async def suggest_invoice_actions() -> dict:
    """Suggest actionable items based on invoice analysis."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.suggest_invoice_actions()

# Currency Management Tools

@mcp.tool()
async def list_currencies(active_only: bool = True) -> dict:
    """
    List supported currencies with optional filtering for active currencies only.
    
    Args:
        active_only: Return only active currencies (default: True)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.list_currencies(active_only=active_only)

@mcp.tool()
async def create_currency(code: str, name: str, symbol: str, decimal_places: int = 2, is_active: bool = True) -> dict:
    """
    Create a custom currency for the tenant.
    
    Args:
        code: Currency code (e.g., USD, EUR)
        name: Currency name
        symbol: Currency symbol
        decimal_places: Number of decimal places (default: 2)
        is_active: Whether the currency is active (default: True)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.create_currency(code=code, name=name, symbol=symbol, decimal_places=decimal_places, is_active=is_active)

@mcp.tool()
async def convert_currency(amount: float, from_currency: str, to_currency: str, conversion_date: Optional[str] = None) -> dict:
    """
    Convert amount from one currency to another using current or historical exchange rates.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        conversion_date: Date for conversion rate in YYYY-MM-DD format (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.convert_currency(amount=amount, from_currency=from_currency, to_currency=to_currency, conversion_date=conversion_date)

# Payment Management Tools

@mcp.tool()
async def list_payments(skip: int = 0, limit: int = 100) -> dict:
    """
    List all payments with pagination support.
    
    Args:
        skip: Number of payments to skip for pagination (default: 0)
        limit: Maximum number of payments to return (default: 100)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.list_payments(skip=skip, limit=limit)

@mcp.tool()
async def query_payments(query: str) -> dict:
    """
    Query payments using natural language (e.g., 'payments yesterday', 'payments this week', 'cash payments over $100').
    
    Args:
        query: Natural language query describing the payments to find
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.query_payments(query=query)

@mcp.tool()
async def create_payment(invoice_id: int, amount: float, payment_date: str, payment_method: str, reference: Optional[str] = None, notes: Optional[str] = None) -> dict:
    """
    Create a new payment for an invoice.
    
    Args:
        invoice_id: ID of the invoice this payment is for
        amount: Payment amount
        payment_date: Payment date in ISO format (YYYY-MM-DD)
        payment_method: Payment method (cash, check, credit_card, etc.)
        reference: Payment reference number (optional)
        notes: Additional notes (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.create_payment(invoice_id=invoice_id, amount=amount, payment_date=payment_date, payment_method=payment_method, reference=reference, notes=notes)

# Inventory Management Tools

@mcp.tool()
async def list_inventory_categories(active_only: bool = True) -> dict:
    """
    List all inventory categories with optional filtering for active categories only.

    Args:
        active_only: Return only active categories (default: True)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.list_inventory_categories(active_only=active_only)

@mcp.tool()
async def create_inventory_category(name: str, description: Optional[str] = None, is_active: bool = True) -> dict:
    """
    Create a new inventory category for organizing inventory items.

    Args:
        name: Category name
        description: Category description (optional)
        is_active: Whether category is active (default: True)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.create_inventory_category(name=name, description=description, is_active=is_active)

@mcp.tool()
async def update_inventory_category(category_id: int, name: Optional[str] = None, description: Optional[str] = None, is_active: Optional[bool] = None) -> dict:
    """
    Update an existing inventory category.

    Args:
        category_id: ID of category to update
        name: New category name (optional)
        description: New category description (optional)
        is_active: New active status (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.update_inventory_category(category_id=category_id, name=name, description=description, is_active=is_active)

@mcp.tool()
async def list_inventory_items(skip: int = 0, limit: int = 100, query: Optional[str] = None, category_id: Optional[int] = None, item_type: Optional[str] = None, low_stock_only: bool = False, track_stock: Optional[bool] = None) -> dict:
    """
    List inventory items with optional filtering and pagination.

    Args:
        skip: Number of items to skip for pagination (default: 0)
        limit: Maximum number of items to return (default: 100)
        query: Search query for items (optional)
        category_id: Filter by category ID (optional)
        item_type: Filter by item type (optional)
        low_stock_only: Return only low stock items (default: False)
        track_stock: Filter by stock tracking setting (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.list_inventory_items(skip=skip, limit=limit, query=query, category_id=category_id, item_type=item_type, low_stock_only=low_stock_only, track_stock=track_stock)

@mcp.tool()
async def create_inventory_item(name: str, unit_price: float, sku: Optional[str] = None, description: Optional[str] = None, category_id: Optional[int] = None, cost_price: Optional[float] = None, currency: str = "USD", track_stock: bool = True, current_stock: float = 0, minimum_stock: float = 0, unit_of_measure: str = "each", item_type: str = "product", is_active: bool = True) -> dict:
    """
    Create a new inventory item with detailed specifications.

    Args:
        name: Item name
        unit_price: Unit selling price
        sku: Stock Keeping Unit (optional)
        description: Item description (optional)
        category_id: Category ID (optional)
        cost_price: Unit cost price (optional)
        currency: Currency code (default: USD)
        track_stock: Whether to track stock levels (default: True)
        current_stock: Current stock quantity (default: 0)
        minimum_stock: Minimum stock level (default: 0)
        unit_of_measure: Unit of measure (default: "each")
        item_type: Type of item (default: "product")
        is_active: Whether item is active (default: True)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.create_inventory_item(name=name, unit_price=unit_price, sku=sku, description=description, category_id=category_id, cost_price=cost_price, currency=currency, track_stock=track_stock, current_stock=current_stock, minimum_stock=minimum_stock, unit_of_measure=unit_of_measure, item_type=item_type, is_active=is_active)

@mcp.tool()
async def update_inventory_item(item_id: int, name: Optional[str] = None, sku: Optional[str] = None, description: Optional[str] = None, category_id: Optional[int] = None, unit_price: Optional[float] = None, cost_price: Optional[float] = None, currency: Optional[str] = None, track_stock: Optional[bool] = None, current_stock: Optional[float] = None, minimum_stock: Optional[float] = None, unit_of_measure: Optional[str] = None, item_type: Optional[str] = None, is_active: Optional[bool] = None) -> dict:
    """
    Update an existing inventory item.

    Args:
        item_id: ID of item to update
        name: New item name (optional)
        sku: New SKU (optional)
        description: New description (optional)
        category_id: New category ID (optional)
        unit_price: New unit price (optional)
        cost_price: New cost price (optional)
        currency: New currency (optional)
        track_stock: New stock tracking setting (optional)
        current_stock: New current stock (optional)
        minimum_stock: New minimum stock (optional)
        unit_of_measure: New unit of measure (optional)
        item_type: New item type (optional)
        is_active: New active status (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.update_inventory_item(item_id=item_id, name=name, sku=sku, description=description, category_id=category_id, unit_price=unit_price, cost_price=cost_price, currency=currency, track_stock=track_stock, current_stock=current_stock, minimum_stock=minimum_stock, unit_of_measure=unit_of_measure, item_type=item_type, is_active=is_active)

@mcp.tool()
async def adjust_stock(item_id: int, quantity: float, reason: str = "Manual adjustment") -> dict:
    """
    Adjust stock levels for an inventory item manually.

    Args:
        item_id: ID of inventory item
        quantity: Quantity to adjust (positive for increase, negative for decrease)
        reason: Reason for adjustment (default: "Manual adjustment")
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.adjust_stock(item_id=item_id, quantity=quantity, reason=reason)

@mcp.tool()
async def get_inventory_analytics() -> dict:
    """
    Get comprehensive inventory analytics and statistics including totals, low stock alerts, and category breakdowns.
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.get_inventory_analytics()

@mcp.tool()
async def get_low_stock_items() -> dict:
    """
    Get items with stock levels below their minimum threshold.
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.get_low_stock_items()

# Bank Statement Management Tools

@mcp.tool()
async def list_bank_statements(skip: int = 0, limit: int = 100, status: Optional[str] = None, account_name: Optional[str] = None) -> dict:
    """
    List bank statements with optional filtering and pagination.

    Args:
        skip: Number of statements to skip for pagination (default: 0)
        limit: Maximum number of statements to return (default: 100)
        status: Filter by processing status (optional)
        account_name: Filter by account name (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.list_bank_statements(skip=skip, limit=limit, status=status, account_name=account_name)

@mcp.tool()
async def get_bank_statement(statement_id: int) -> dict:
    """
    Get detailed information about a bank statement including all transactions.

    Args:
        statement_id: ID of bank statement to retrieve
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.get_bank_statement(statement_id=statement_id)

@mcp.tool()
async def reprocess_bank_statement(statement_id: int, force_reprocess: bool = False) -> dict:
    """
    Reprocess a bank statement to extract transactions again.

    Args:
        statement_id: ID of bank statement to reprocess
        force_reprocess: Force reprocessing even if already processed (default: False)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.reprocess_bank_statement(statement_id=statement_id, force_reprocess=force_reprocess)

@mcp.tool()
async def update_bank_statement_meta(statement_id: int, account_name: Optional[str] = None, statement_period: Optional[str] = None, notes: Optional[str] = None, status: Optional[str] = None) -> dict:
    """
    Update bank statement metadata like account name, period, notes, and status.

    Args:
        statement_id: ID of bank statement to update
        account_name: Bank account name (optional)
        statement_period: Statement period description (optional)
        notes: Additional notes (optional)
        status: Processing status (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.update_bank_statement_meta(statement_id=statement_id, account_name=account_name, statement_period=statement_period, notes=notes, status=status)

@mcp.tool()
async def delete_bank_statement(statement_id: int, confirm_deletion: bool = False) -> dict:
    """
    Delete a bank statement and all associated transactions.

    Args:
        statement_id: ID of bank statement to delete
        confirm_deletion: Confirmation flag to prevent accidental deletion (default: False)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.delete_bank_statement(statement_id=statement_id, confirm_deletion=confirm_deletion)

# Expense Management Tools

@mcp.tool()
async def list_expenses(skip: int = 0, limit: int = 100, category: Optional[str] = None, invoice_id: Optional[int] = None, unlinked_only: bool = False) -> dict:
    """
    List expenses with optional filters and pagination.
    
    Args:
        skip: Number of expenses to skip (default: 0)
        limit: Max number of expenses to return (default: 100)
        category: Filter by category (optional)
        invoice_id: Filter by linked invoice id (optional)
        unlinked_only: Return only expenses not linked to any invoice (default: False)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await server_context.tools.list_expenses(skip=skip, limit=limit, category=category, invoice_id=invoice_id, unlinked_only=unlinked_only)

@mcp.tool()
async def get_expense(expense_id: int) -> dict:
    """Get a specific expense by ID."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await server_context.tools.get_expense(expense_id=expense_id)

@mcp.tool()
async def create_expense(
    amount: float,
    currency: str,
    expense_date: str,
    category: str,
    vendor: Optional[str] = None,
    tax_rate: Optional[float] = None,
    tax_amount: Optional[float] = None,
    total_amount: Optional[float] = None,
    payment_method: Optional[str] = None,
    reference_number: Optional[str] = None,
    status: Optional[str] = "recorded",
    notes: Optional[str] = None,
    invoice_id: Optional[int] = None,
) -> dict:
    """Create a new expense."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await server_context.tools.create_expense(
        amount=amount,
        currency=currency,
        expense_date=expense_date,
        category=category,
        vendor=vendor,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_amount=total_amount,
        payment_method=payment_method,
        reference_number=reference_number,
        status=status,
        notes=notes,
        invoice_id=invoice_id,
    )

@mcp.tool()
async def update_expense(
    expense_id: int,
    amount: Optional[float] = None,
    currency: Optional[str] = None,
    expense_date: Optional[str] = None,
    category: Optional[str] = None,
    vendor: Optional[str] = None,
    tax_rate: Optional[float] = None,
    tax_amount: Optional[float] = None,
    total_amount: Optional[float] = None,
    payment_method: Optional[str] = None,
    reference_number: Optional[str] = None,
    status: Optional[str] = None,
    notes: Optional[str] = None,
    invoice_id: Optional[int] = None,
) -> dict:
    """Update an existing expense."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await server_context.tools.update_expense(
        expense_id=expense_id,
        amount=amount,
        currency=currency,
        expense_date=expense_date,
        category=category,
        vendor=vendor,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_amount=total_amount,
        payment_method=payment_method,
        reference_number=reference_number,
        status=status,
        notes=notes,
        invoice_id=invoice_id,
    )

@mcp.tool()
async def delete_expense(expense_id: int) -> dict:
    """Delete an expense by ID."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await server_context.tools.delete_expense(expense_id=expense_id)

@mcp.tool()
async def upload_expense_receipt(expense_id: int, file_path: str, filename: Optional[str] = None, content_type: Optional[str] = None) -> dict:
    """Upload a receipt file for an expense."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await server_context.tools.upload_expense_receipt(expense_id=expense_id, file_path=file_path, filename=filename, content_type=content_type)

@mcp.tool()
async def list_expense_attachments(expense_id: int) -> dict:
    """List attachments for an expense."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await server_context.tools.list_expense_attachments(expense_id=expense_id)

@mcp.tool()
async def delete_expense_attachment(expense_id: int, attachment_id: int) -> dict:
    """Delete an attachment for an expense."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await server_context.tools.delete_expense_attachment(expense_id=expense_id, attachment_id=attachment_id)

# Statement Management Tools

@mcp.tool()
async def list_statements() -> dict:
    """List all statements with their processing status and metadata."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await server_context.tools.list_statements()

@mcp.tool()
async def get_bank_statement(statement_id: int) -> dict:
    """Get a specific bank statement with all its transactions."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await server_context.tools.get_bank_statement(statement_id=statement_id)

@mcp.tool()
async def reprocess_bank_statement(statement_id: int) -> dict:
    """Reprocess a bank statement to extract transactions again."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await server_context.tools.reprocess_bank_statement(statement_id=statement_id)

@mcp.tool()
async def update_bank_statement_meta(statement_id: int, notes: Optional[str] = None, labels: Optional[List[str]] = None) -> dict:
    """Update bank statement metadata like notes and labels."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await server_context.tools.update_bank_statement_meta(statement_id=statement_id, notes=notes, labels=labels)

@mcp.tool()
async def delete_bank_statement(statement_id: int) -> dict:
    """Delete a bank statement and its associated file."""
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    return await server_context.tools.delete_bank_statement(statement_id=statement_id)
# Settings Tools

@mcp.tool()
async def get_settings() -> dict:
    """
    Get tenant settings including company information and invoice settings.
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.get_settings()

# Discount Rules Tools

@mcp.tool()
async def list_discount_rules() -> dict:
    """
    List all discount rules for the current tenant.
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.list_discount_rules()

@mcp.tool()
async def create_discount_rule(name: str, discount_type: str, discount_value: float, min_amount: Optional[float] = None, max_discount: Optional[float] = None, priority: int = 1, is_active: bool = True, currency: Optional[str] = None) -> dict:
    """
    Create a new discount rule for the tenant.
    
    Args:
        name: Name of the discount rule
        discount_type: Type of discount (percentage, fixed)
        discount_value: Discount value
        min_amount: Minimum amount for discount to apply (optional)
        max_discount: Maximum discount amount (optional)
        priority: Priority of the rule, higher number = higher priority (default: 1)
        is_active: Whether the rule is active (default: True)
        currency: Currency code for the rule (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    # Validate discount_type
    if discount_type not in ["percentage", "fixed"]:
        return {"success": False, "error": "discount_type must be either 'percentage' or 'fixed'"}
    
    return await server_context.tools.create_discount_rule(name=name, discount_type=discount_type, discount_value=discount_value, min_amount=min_amount, max_discount=max_discount, priority=priority, is_active=is_active, currency=currency)

# CRM Tools

@mcp.tool()
async def create_client_note(client_id: int, title: str, content: str, note_type: str = "general") -> dict:
    """
    Create a note for a client.
    
    Args:
        client_id: ID of the client
        title: Note title
        content: Note content
        note_type: Type of note (general, call, meeting, etc.) (default: "general")
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.create_client_note(client_id=client_id, title=title, content=content, note_type=note_type)

# Email Tools

@mcp.tool()
async def send_invoice_email(invoice_id: int, to_email: Optional[str] = None, to_name: Optional[str] = None, subject: Optional[str] = None, message: Optional[str] = None) -> dict:
    """
    Send an invoice via email.
    
    Args:
        invoice_id: ID of the invoice to send
        to_email: Recipient email address (optional, uses client email if not provided)
        to_name: Recipient name (optional, uses client name if not provided)
        subject: Email subject (optional)
        message: Custom message (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.send_invoice_email(invoice_id=invoice_id, to_email=to_email, to_name=to_name, subject=subject, message=message)

@mcp.tool()
async def test_email_configuration(test_email: str) -> dict:
    """
    Test email configuration by sending a test email.
    
    Args:
        test_email: Email address to send test email to
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.test_email_configuration(test_email=test_email)

# Tenant Tools

@mcp.tool()
async def get_tenant_info() -> dict:
    """
    Get current tenant information including company details and settings.
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}
    
    return await server_context.tools.get_tenant_info()

# AI Configuration Tools

@mcp.tool()
async def list_ai_configs() -> dict:
    """
    List all AI configurations for the current tenant. Returns configuration details including providers, models, and settings.
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.list_ai_configs()

@mcp.tool()
async def create_ai_config(provider_name: str, model_name: str, provider_url: Optional[str] = None, api_key: Optional[str] = None, is_active: bool = True, is_default: bool = False, ocr_enabled: bool = False, max_tokens: int = 4096, temperature: float = 0.1) -> dict:
    """
    Create a new AI configuration for the tenant.

    Args:
        provider_name: AI provider name (openai, anthropic, ollama, google, custom)
        model_name: Model name to use
        provider_url: Provider URL (for custom providers)
        api_key: API key for the provider
        is_active: Whether the config is active (default: True)
        is_default: Whether this is the default config (default: False)
        ocr_enabled: Whether OCR is enabled for this config (default: False)
        max_tokens: Maximum tokens for requests (default: 4096)
        temperature: Temperature for AI responses (default: 0.1)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.create_ai_config(provider_name=provider_name, model_name=model_name, provider_url=provider_url, api_key=api_key, is_active=is_active, is_default=is_default, ocr_enabled=ocr_enabled, max_tokens=max_tokens, temperature=temperature)

@mcp.tool()
async def update_ai_config(config_id: int, provider_name: Optional[str] = None, model_name: Optional[str] = None, provider_url: Optional[str] = None, api_key: Optional[str] = None, is_active: Optional[bool] = None, is_default: Optional[bool] = None, ocr_enabled: Optional[bool] = None, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> dict:
    """
    Update an existing AI configuration.

    Args:
        config_id: ID of the AI config to update
        provider_name: AI provider name (optional)
        model_name: Model name to use (optional)
        provider_url: Provider URL (optional)
        api_key: API key for the provider (optional)
        is_active: Whether the config is active (optional)
        is_default: Whether this is the default config (optional)
        ocr_enabled: Whether OCR is enabled for this config (optional)
        max_tokens: Maximum tokens for requests (optional)
        temperature: Temperature for AI responses (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.update_ai_config(config_id=config_id, provider_name=provider_name, model_name=model_name, provider_url=provider_url, api_key=api_key, is_active=is_active, is_default=is_default, ocr_enabled=ocr_enabled, max_tokens=max_tokens, temperature=temperature)

@mcp.tool()
async def test_ai_config(config_id: int, custom_prompt: Optional[str] = None, test_text: Optional[str] = None) -> dict:
    """
    Test an AI configuration to ensure it's working properly.

    Args:
        config_id: ID of the AI config to test
        custom_prompt: Custom test prompt (optional)
        test_text: Test text for processing (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.test_ai_config(config_id=config_id, custom_prompt=custom_prompt, test_text=test_text)

# Analytics Tools

@mcp.tool()
async def get_page_views_analytics(days: int = 7, path_filter: Optional[str] = None) -> dict:
    """
    Get page view analytics for the current tenant.

    Args:
        days: Number of days to look back (default: 7)
        path_filter: Filter by path (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.get_page_views_analytics(days=days, path_filter=path_filter)

# Audit Log Tools

@mcp.tool()
async def get_audit_logs(user_id: Optional[int] = None, user_email: Optional[str] = None, action: Optional[str] = None, resource_type: Optional[str] = None, resource_id: Optional[str] = None, status: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 100, offset: int = 0) -> dict:
    """
    Get audit logs with optional filters for tracking system activities.

    Args:
        user_id: Filter by user ID (optional)
        user_email: Filter by user email (optional)
        action: Filter by action (optional)
        resource_type: Filter by resource type (optional)
        resource_id: Filter by resource ID (optional)
        status: Filter by status (optional)
        start_date: Start date (YYYY-MM-DD) (optional)
        end_date: End date (YYYY-MM-DD) (optional)
        limit: Maximum number of results (default: 100)
        offset: Number of results to skip (default: 0)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.get_audit_logs(user_id=user_id, user_email=user_email, action=action, resource_type=resource_type, resource_id=resource_id, status=status, start_date=start_date, end_date=end_date, limit=limit, offset=offset)

# Notification Tools

@mcp.tool()
async def get_notification_settings() -> dict:
    """
    Get current user's notification settings.
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.get_notification_settings()

@mcp.tool()
async def update_notification_settings(invoice_created: bool = True, invoice_paid: bool = True, payment_received: bool = True, client_created: bool = False, overdue_invoice: bool = True, email_enabled: bool = True) -> dict:
    """
    Update current user's notification settings.

    Args:
        invoice_created: Notify when invoices are created (default: True)
        invoice_paid: Notify when invoices are paid (default: True)
        payment_received: Notify when payments are received (default: True)
        client_created: Notify when clients are created (default: False)
        overdue_invoice: Notify about overdue invoices (default: True)
        email_enabled: Enable email notifications (default: True)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.update_notification_settings(invoice_created=invoice_created, invoice_paid=invoice_paid, payment_received=payment_received, client_created=client_created, overdue_invoice=overdue_invoice, email_enabled=email_enabled)

# PDF Processing Tools

@mcp.tool()
async def get_ai_status() -> dict:
    """
    Get AI status for PDF processing to check if AI is configured and available.
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.get_ai_status()

@mcp.tool()
async def process_pdf_upload(file_path: str, filename: Optional[str] = None) -> dict:
    """
    Upload and process a PDF file using AI for invoice data extraction.

    Args:
        file_path: Path to the PDF file to upload
        filename: Override filename (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.process_pdf_upload(file_path=file_path, filename=filename)

# Tax Integration Tools

@mcp.tool()
async def get_tax_integration_status() -> dict:
    """
    Get tax service integration status to check if tax service is configured and connected.
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.get_tax_integration_status()

@mcp.tool()
async def send_to_tax_service(item_id: int, item_type: str) -> dict:
    """
    Send an item (expense or invoice) to the tax service for processing.

    Args:
        item_id: ID of the item to send
        item_type: Type of item (expense or invoice)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.send_to_tax_service(item_id=item_id, item_type=item_type)

@mcp.tool()
async def bulk_send_to_tax_service(item_ids: List[int], item_type: str) -> dict:
    """
    Bulk send multiple items to the tax service for processing.

    Args:
        item_ids: List of item IDs to send
        item_type: Type of items (expense or invoice)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.bulk_send_to_tax_service(item_ids=item_ids, item_type=item_type)

@mcp.tool()
async def get_tax_service_transactions() -> dict:
    """
    Get tax service transactions to view items that have been sent to the tax service.
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.get_tax_service_transactions()

# Super Admin Tools

@mcp.tool()
async def get_tenant_stats(tenant_id: int) -> dict:
    """
    Get detailed statistics for a specific tenant including user count, clients, invoices, and payments.

    Args:
        tenant_id: ID of the tenant to get statistics for
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.get_tenant_stats(tenant_id=tenant_id)

@mcp.tool()
async def create_tenant(name: str, domain: str, company_name: Optional[str] = None, logo_url: Optional[str] = None, is_active: bool = True, max_users: Optional[int] = None, subscription_plan: Optional[str] = None) -> dict:
    """
    Create a new tenant with the specified configuration.

    Args:
        name: Tenant name
        domain: Tenant domain
        company_name: Company name (optional)
        logo_url: Logo URL (optional)
        is_active: Whether tenant is active (default: True)
        max_users: Maximum number of users (optional)
        subscription_plan: Subscription plan (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.create_tenant(name=name, domain=domain, company_name=company_name, logo_url=logo_url, is_active=is_active, max_users=max_users, subscription_plan=subscription_plan)

@mcp.tool()
async def update_tenant(tenant_id: int, name: Optional[str] = None, domain: Optional[str] = None, company_name: Optional[str] = None, logo_url: Optional[str] = None, is_active: Optional[bool] = None, max_users: Optional[int] = None, subscription_plan: Optional[str] = None) -> dict:
    """
    Update tenant information.

    Args:
        tenant_id: ID of the tenant to update
        name: Tenant name (optional)
        domain: Tenant domain (optional)
        company_name: Company name (optional)
        logo_url: Logo URL (optional)
        is_active: Whether tenant is active (optional)
        max_users: Maximum number of users (optional)
        subscription_plan: Subscription plan (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.update_tenant(tenant_id=tenant_id, name=name, domain=domain, company_name=company_name, logo_url=logo_url, is_active=is_active, max_users=max_users, subscription_plan=subscription_plan)

@mcp.tool()
async def delete_tenant(tenant_id: int) -> dict:
    """
    Delete a tenant and all associated data.

    Args:
        tenant_id: ID of the tenant to delete
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.delete_tenant(tenant_id=tenant_id)

@mcp.tool()
async def list_tenant_users(tenant_id: int, skip: int = 0, limit: int = 100) -> dict:
    """
    List all users in a specific tenant.

    Args:
        tenant_id: ID of the tenant
        skip: Number of users to skip for pagination (default: 0)
        limit: Maximum number of users to return (default: 100)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.list_tenant_users(tenant_id=tenant_id, skip=skip, limit=limit)

@mcp.tool()
async def create_tenant_user(tenant_id: int, email: str, first_name: str, last_name: str, role: str = "user", is_active: bool = True) -> dict:
    """
    Create a new user in a specific tenant.

    Args:
        tenant_id: ID of the tenant
        email: User email address
        first_name: User's first name
        last_name: User's last name
        role: User role (default: "user")
        is_active: Whether user is active (default: True)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.create_tenant_user(tenant_id=tenant_id, email=email, first_name=first_name, last_name=last_name, role=role, is_active=is_active)

@mcp.tool()
async def update_tenant_user(tenant_id: int, user_id: int, email: Optional[str] = None, first_name: Optional[str] = None, last_name: Optional[str] = None, role: Optional[str] = None, is_active: Optional[bool] = None) -> dict:
    """
    Update a user in a specific tenant.

    Args:
        tenant_id: ID of the tenant
        user_id: ID of the user to update
        email: User email address (optional)
        first_name: User's first name (optional)
        last_name: User's last name (optional)
        role: User role (optional)
        is_active: Whether user is active (optional)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.update_tenant_user(tenant_id=tenant_id, user_id=user_id, email=email, first_name=first_name, last_name=last_name, role=role, is_active=is_active)

@mcp.tool()
async def delete_tenant_user(tenant_id: int, user_id: int) -> dict:
    """
    Delete a user from a specific tenant.

    Args:
        tenant_id: ID of the tenant
        user_id: ID of the user to delete
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.delete_tenant_user(tenant_id=tenant_id, user_id=user_id)

@mcp.tool()
async def promote_user_to_admin(email: str) -> dict:
    """
    Promote a user to admin role.

    Args:
        email: Email address of the user to promote
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.promote_user_to_admin(email=email)

@mcp.tool()
async def reset_user_password(user_id: int, new_password: str, confirm_password: str, force_reset_on_login: bool = False) -> dict:
    """
    Reset a user's password.

    Args:
        user_id: ID of the user
        new_password: New password
        confirm_password: Confirm new password
        force_reset_on_login: Force password reset on login (default: False)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.reset_user_password(user_id=user_id, new_password=new_password, confirm_password=confirm_password, force_reset_on_login=force_reset_on_login)

@mcp.tool()
async def get_system_stats() -> dict:
    """
    Get system-wide statistics across all tenants.
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.get_system_stats()

@mcp.tool()
async def export_tenant_data(tenant_id: int, include_attachments: bool = False) -> dict:
    """
    Export all data for a specific tenant.

    Args:
        tenant_id: ID of the tenant to export
        include_attachments: Include attachments in export (default: False)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.export_tenant_data(tenant_id=tenant_id, include_attachments=include_attachments)

@mcp.tool()
async def import_tenant_data(tenant_id: int, data: Dict[str, Any]) -> dict:
    """
    Import data into a specific tenant.

    Args:
        tenant_id: ID of the tenant to import into
        data: Data to import (JSON format)
    """
    if server_context.tools is None:
        return {"success": False, "error": "Server not properly initialized"}

    return await server_context.tools.import_tenant_data(tenant_id=tenant_id, data=data)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Invoice Application FastMCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  INVOICE_API_BASE_URL    Base URL for the Invoice API (default: http://localhost:8000/api)
  INVOICE_API_EMAIL       Email for API authentication
  INVOICE_API_PASSWORD    Password for API authentication
  REQUEST_TIMEOUT         HTTP request timeout in seconds (default: 30)
  DEFAULT_PAGE_SIZE       Default pagination size (default: 100)
  MAX_PAGE_SIZE          Maximum pagination size (default: 1000)

Examples:
  # Run with default settings
  python -m MCP
  
  # Run with custom API URL
  python -m MCP --api-url http://api.mycompany.com/api
  
  # Run with custom credentials
  python -m MCP --email user@example.com --password mypassword

Available Tools:
  - list_clients: List all clients with pagination
  - search_clients: Search clients by name, email, phone, or address
  - get_client: Get detailed client information by ID
  - create_client: Create a new client
  - list_invoices: List all invoices with pagination
  - search_invoices: Search invoices by various fields
  - get_invoice: Get detailed invoice information by ID
  - create_invoice: Create a new invoice
  - list_expenses: List expenses with optional filters
  - get_expense: Get expense by ID
  - create_expense: Create a new expense
  - update_expense: Update an expense
  - delete_expense: Delete an expense
  - upload_expense_receipt: Upload a receipt for an expense
  - list_expense_attachments: List attachments for an expense
  - delete_expense_attachment: Delete an attachment for an expense
  - list_bank_statements: List bank statements with optional filtering
  - get_bank_statement: Get bank statement with transactions
  - reprocess_bank_statement: Reprocess a bank statement
  - update_bank_statement_meta: Update bank statement metadata
  - delete_bank_statement: Delete a bank statement
  - get_clients_with_outstanding_balance: Get clients with unpaid invoices
  - get_overdue_invoices: Get invoices past their due date
  - get_invoice_stats: Get overall invoice statistics
  - list_inventory_categories: List all inventory categories
  - create_inventory_category: Create a new inventory category
  - update_inventory_category: Update an inventory category
  - list_inventory_items: List inventory items with filtering
  - create_inventory_item: Create a new inventory item
  - update_inventory_item: Update an inventory item
  - adjust_stock: Adjust stock levels for an item
  - get_inventory_analytics: Get inventory analytics
  - get_low_stock_items: Get items with low stock
  - list_currencies: List supported currencies
  - create_currency: Create a custom currency
  - convert_currency: Convert amount between currencies
  - list_payments: List all payments with pagination
  - create_payment: Create a new payment
  - get_settings: Get tenant settings
  - list_discount_rules: List all discount rules
  - create_discount_rule: Create a new discount rule
  - create_client_note: Create a note for a client
  - send_invoice_email: Send an invoice via email
  - test_email_configuration: Test email configuration
  - get_tenant_info: Get current tenant information
  - list_ai_configs: List all AI configurations
  - create_ai_config: Create a new AI configuration
  - update_ai_config: Update an AI configuration
  - test_ai_config: Test an AI configuration
  - get_page_views_analytics: Get page view analytics
  - get_audit_logs: Get audit logs with filters
  - get_notification_settings: Get notification settings
  - update_notification_settings: Update notification settings
  - get_ai_status: Get AI status for PDF processing
  - process_pdf_upload: Upload and process PDF files
  - get_tax_integration_status: Get tax integration status
  - send_to_tax_service: Send items to tax service
  - bulk_send_to_tax_service: Bulk send items to tax service
  - get_tax_service_transactions: Get tax service transactions
  - get_tenant_stats: Get detailed tenant statistics
  - create_tenant: Create a new tenant
  - update_tenant: Update tenant information
  - delete_tenant: Delete a tenant
  - list_tenant_users: List users in a tenant
  - create_tenant_user: Create a user in a tenant
  - update_tenant_user: Update a user in a tenant
  - delete_tenant_user: Delete a user from a tenant
  - promote_user_to_admin: Promote user to admin
  - reset_user_password: Reset user password
  - get_system_stats: Get system-wide statistics
  - export_tenant_data: Export tenant data
  - import_tenant_data: Import data into tenant
        """
    )
    
    parser.add_argument(
        "--api-url",
        help="Base URL for the Invoice API",
        default=config.API_BASE_URL
    )
    parser.add_argument(
        "--email",
        help="Email for API authentication",
        default=config.DEFAULT_EMAIL
    )
    parser.add_argument(
        "--password",
        help="Password for API authentication",
        default=config.DEFAULT_PASSWORD
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def main():
    """Main entry point - simplified to just run FastMCP"""
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

# Legacy compatibility functions - deprecated but kept for backwards compatibility
def main_sync():
    """Legacy sync entry point - use main() instead"""
    import warnings
    warnings.warn("main_sync() is deprecated, use main() instead", DeprecationWarning, stacklevel=2)
    main()

if __name__ == "__main__":
    main() 