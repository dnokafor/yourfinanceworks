"""
FastMCP Tools for Invoice Application
"""
from typing import Any, Dict, List, Optional
import json
from datetime import datetime
import logging
from pydantic import BaseModel, Field

from .api_client import InvoiceAPIClient
from .auth_client import AuthenticationError

logger = logging.getLogger(__name__)


# Tool argument schemas
class ListClientsArgs(BaseModel):
    skip: int = Field(default=0, description="Number of clients to skip for pagination")
    limit: int = Field(default=100, description="Maximum number of clients to return")


class SearchClientsArgs(BaseModel):
    query: str = Field(description="Search query to find clients by name, email, phone, or address")
    skip: int = Field(default=0, description="Number of results to skip for pagination")
    limit: int = Field(default=100, description="Maximum number of results to return")


class GetClientArgs(BaseModel):
    client_id: int = Field(description="ID of the client to retrieve")


class CreateClientArgs(BaseModel):
    name: str = Field(description="Client's full name")
    email: Optional[str] = Field(default=None, description="Client's email address")
    phone: Optional[str] = Field(default=None, description="Client's phone number")
    address: Optional[str] = Field(default=None, description="Client's address")


class ListInvoicesArgs(BaseModel):
    skip: int = Field(default=0, description="Number of invoices to skip for pagination")
    limit: int = Field(default=100, description="Maximum number of invoices to return")


class SearchInvoicesArgs(BaseModel):
    query: str = Field(description="Search query to find invoices by number, client name, status, notes, or amount")
    skip: int = Field(default=0, description="Number of results to skip for pagination")
    limit: int = Field(default=100, description="Maximum number of results to return")


class GetInvoiceArgs(BaseModel):
    invoice_id: int = Field(description="ID of the invoice to retrieve")


class CreateInvoiceArgs(BaseModel):
    client_id: int = Field(description="ID of the client this invoice belongs to")
    amount: float = Field(description="Total amount of the invoice")
    due_date: str = Field(description="Due date of the invoice in ISO format (YYYY-MM-DD)")
    status: str = Field(default="draft", description="Status of the invoice (draft, sent, paid, etc.)")
    notes: Optional[str] = Field(default=None, description="Additional notes for the invoice")


# Expenses
class ListExpensesArgs(BaseModel):
    skip: int = Field(default=0, description="Number of expenses to skip for pagination")
    limit: int = Field(default=100, description="Maximum number of expenses to return")
    category: Optional[str] = Field(default=None, description="Filter by category")
    invoice_id: Optional[int] = Field(default=None, description="Filter by linked invoice id")
    unlinked_only: bool = Field(default=False, description="Return only expenses not linked to any invoice")


class CreateExpenseArgs(BaseModel):
    amount: float = Field(description="Expense amount before tax")
    currency: str = Field(default="USD", description="Currency code for the expense")
    expense_date: str = Field(description="Expense date in ISO format (YYYY-MM-DD)")
    category: str = Field(description="Expense category")
    vendor: Optional[str] = Field(default=None, description="Vendor or payee")
    tax_rate: Optional[float] = Field(default=None, description="Tax rate percentage")
    tax_amount: Optional[float] = Field(default=None, description="Calculated tax amount, if provided")
    total_amount: Optional[float] = Field(default=None, description="Total amount including tax")
    payment_method: Optional[str] = Field(default=None, description="Payment method")
    reference_number: Optional[str] = Field(default=None, description="Reference number")
    status: Optional[str] = Field(default="recorded", description="Status of the expense")
    notes: Optional[str] = Field(default=None, description="Notes about the expense")
    invoice_id: Optional[int] = Field(default=None, description="Linked invoice ID, if any")


class UpdateExpenseArgs(BaseModel):
    expense_id: int = Field(description="ID of the expense to update")
    amount: Optional[float] = Field(default=None)
    currency: Optional[str] = Field(default=None)
    expense_date: Optional[str] = Field(default=None, description="ISO date YYYY-MM-DD")
    category: Optional[str] = Field(default=None)
    vendor: Optional[str] = Field(default=None)
    tax_rate: Optional[float] = Field(default=None)
    tax_amount: Optional[float] = Field(default=None)
    total_amount: Optional[float] = Field(default=None)
    payment_method: Optional[str] = Field(default=None)
    reference_number: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    invoice_id: Optional[int] = Field(default=None)


class UploadExpenseReceiptArgs(BaseModel):
    expense_id: int = Field(description="ID of the expense")
    file_path: str = Field(description="Absolute path to the file to upload")
    filename: Optional[str] = Field(default=None, description="Override filename")
    content_type: Optional[str] = Field(default=None, description="Explicit content type")


# Currency Management
class ListCurrenciesArgs(BaseModel):
    active_only: bool = Field(default=True, description="Return only active currencies")


class CreateCurrencyArgs(BaseModel):
    code: str = Field(description="Currency code (e.g., USD, EUR)")
    name: str = Field(description="Currency name")
    symbol: str = Field(description="Currency symbol")
    decimal_places: int = Field(default=2, description="Number of decimal places")
    is_active: bool = Field(default=True, description="Whether the currency is active")


class ConvertCurrencyArgs(BaseModel):
    amount: float = Field(description="Amount to convert")
    from_currency: str = Field(description="Source currency code")
    to_currency: str = Field(description="Target currency code")
    conversion_date: Optional[str] = Field(default=None, description="Date for conversion rate (YYYY-MM-DD)")


# Payments
class ListPaymentsArgs(BaseModel):
    skip: int = Field(default=0, description="Number of payments to skip for pagination")
    limit: int = Field(default=100, description="Maximum number of payments to return")


class CreatePaymentArgs(BaseModel):
    invoice_id: int = Field(description="ID of the invoice this payment is for")
    amount: float = Field(description="Payment amount")
    payment_date: str = Field(description="Payment date in ISO format (YYYY-MM-DD)")
    payment_method: str = Field(description="Payment method (cash, check, credit_card, etc.)")
    reference: Optional[str] = Field(default=None, description="Payment reference number")
    notes: Optional[str] = Field(default=None, description="Additional notes")


# Settings
class GetSettingsArgs(BaseModel):
    pass  # No arguments needed for getting settings


# Discount Rules
class ListDiscountRulesArgs(BaseModel):
    pass  # No arguments needed for listing discount rules


class CreateDiscountRuleArgs(BaseModel):
    name: str = Field(description="Name of the discount rule")
    discount_type: str = Field(description="Type of discount (percentage, fixed)")
    discount_value: float = Field(description="Discount value")
    min_amount: Optional[float] = Field(default=None, description="Minimum amount for discount to apply")
    max_discount: Optional[float] = Field(default=None, description="Maximum discount amount")
    priority: int = Field(default=1, description="Priority of the rule (higher number = higher priority)")
    is_active: bool = Field(default=True, description="Whether the rule is active")
    currency: Optional[str] = Field(default=None, description="Currency code for the rule")


# CRM
class CreateClientNoteArgs(BaseModel):
    client_id: int = Field(description="ID of the client")
    title: str = Field(description="Note title")
    content: str = Field(description="Note content")
    note_type: str = Field(default="general", description="Type of note (general, call, meeting, etc.)")


# Email
class SendInvoiceEmailArgs(BaseModel):
    invoice_id: int = Field(description="ID of the invoice to send")
    to_email: Optional[str] = Field(default=None, description="Recipient email address")
    to_name: Optional[str] = Field(default=None, description="Recipient name")
    subject: Optional[str] = Field(default=None, description="Email subject")
    message: Optional[str] = Field(default=None, description="Custom message")


class TestEmailArgs(BaseModel):
    test_email: str = Field(description="Email address to send test email to")


# Tenant
class GetTenantArgs(BaseModel):
    pass  # No arguments needed for getting tenant info


# AI Configuration
class ListAIConfigsArgs(BaseModel):
    pass  # No arguments needed for listing AI configs


class CreateAIConfigArgs(BaseModel):
    provider_name: str = Field(description="AI provider name (openai, anthropic, ollama, google, custom)")
    provider_url: Optional[str] = Field(default=None, description="Provider URL (for custom providers)")
    api_key: Optional[str] = Field(default=None, description="API key for the provider")
    model_name: str = Field(description="Model name to use")
    is_active: bool = Field(default=True, description="Whether the config is active")
    is_default: bool = Field(default=False, description="Whether this is the default config")
    ocr_enabled: bool = Field(default=False, description="Whether OCR is enabled for this config")
    max_tokens: int = Field(default=4096, description="Maximum tokens for requests")
    temperature: float = Field(default=0.1, description="Temperature for AI responses")


class UpdateAIConfigArgs(BaseModel):
    config_id: int = Field(description="ID of the AI config to update")
    provider_name: Optional[str] = Field(default=None, description="AI provider name")
    provider_url: Optional[str] = Field(default=None, description="Provider URL")
    api_key: Optional[str] = Field(default=None, description="API key")
    model_name: Optional[str] = Field(default=None, description="Model name")
    is_active: Optional[bool] = Field(default=None, description="Whether active")
    is_default: Optional[bool] = Field(default=None, description="Whether default")
    ocr_enabled: Optional[bool] = Field(default=None, description="OCR enabled")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens")
    temperature: Optional[float] = Field(default=None, description="Temperature")


class TestAIConfigArgs(BaseModel):
    config_id: int = Field(description="ID of the AI config to test")
    custom_prompt: Optional[str] = Field(default=None, description="Custom test prompt")
    test_text: Optional[str] = Field(default=None, description="Test text for processing")


# Analytics
class GetPageViewsAnalyticsArgs(BaseModel):
    days: int = Field(default=7, description="Number of days to look back")
    path_filter: Optional[str] = Field(default=None, description="Filter by path")


# Audit Logs
class GetAuditLogsArgs(BaseModel):
    user_id: Optional[int] = Field(default=None, description="Filter by user ID")
    user_email: Optional[str] = Field(default=None, description="Filter by user email")
    action: Optional[str] = Field(default=None, description="Filter by action")
    resource_type: Optional[str] = Field(default=None, description="Filter by resource type")
    resource_id: Optional[str] = Field(default=None, description="Filter by resource ID")
    status: Optional[str] = Field(default=None, description="Filter by status")
    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")
    limit: int = Field(default=100, description="Maximum number of results")
    offset: int = Field(default=0, description="Number of results to skip")


# Notifications
class GetNotificationSettingsArgs(BaseModel):
    pass  # No arguments needed


class UpdateNotificationSettingsArgs(BaseModel):
    invoice_created: bool = Field(default=True, description="Notify when invoices are created")
    invoice_paid: bool = Field(default=True, description="Notify when invoices are paid")
    payment_received: bool = Field(default=True, description="Notify when payments are received")
    client_created: bool = Field(default=False, description="Notify when clients are created")
    overdue_invoice: bool = Field(default=True, description="Notify about overdue invoices")
    email_enabled: bool = Field(default=True, description="Enable email notifications")


# PDF Processing
class GetAIStatusArgs(BaseModel):
    pass  # No arguments needed


class ProcessPDFUploadArgs(BaseModel):
    file_path: str = Field(description="Path to the PDF file to upload")
    filename: Optional[str] = Field(default=None, description="Override filename")


# Tax Integration
class GetTaxIntegrationStatusArgs(BaseModel):
    pass  # No arguments needed


class SendToTaxServiceArgs(BaseModel):
    item_id: int = Field(description="ID of the item to send")
    item_type: str = Field(description="Type of item (expense or invoice)")


class BulkSendToTaxServiceArgs(BaseModel):
    item_ids: List[int] = Field(description="List of item IDs to send")
    item_type: str = Field(description="Type of items (expense or invoice)")


# Super Admin Tools
class GetTenantStatsArgs(BaseModel):
    tenant_id: int = Field(description="ID of the tenant to get stats for")


class CreateTenantArgs(BaseModel):
    name: str = Field(description="Tenant name")
    domain: str = Field(description="Tenant domain")
    company_name: Optional[str] = Field(default=None, description="Company name")
    logo_url: Optional[str] = Field(default=None, description="Logo URL")
    is_active: bool = Field(default=True, description="Whether tenant is active")
    max_users: Optional[int] = Field(default=None, description="Maximum number of users")
    subscription_plan: Optional[str] = Field(default=None, description="Subscription plan")


class UpdateTenantArgs(BaseModel):
    tenant_id: int = Field(description="ID of the tenant to update")
    name: Optional[str] = Field(default=None, description="Tenant name")
    domain: Optional[str] = Field(default=None, description="Tenant domain")
    company_name: Optional[str] = Field(default=None, description="Company name")
    logo_url: Optional[str] = Field(default=None, description="Logo URL")
    is_active: Optional[bool] = Field(default=None, description="Whether tenant is active")
    max_users: Optional[int] = Field(default=None, description="Maximum number of users")
    subscription_plan: Optional[str] = Field(default=None, description="Subscription plan")


class ListTenantUsersArgs(BaseModel):
    tenant_id: int = Field(description="ID of the tenant")
    skip: int = Field(default=0, description="Number of users to skip")
    limit: int = Field(default=100, description="Maximum number of users to return")


class CreateTenantUserArgs(BaseModel):
    tenant_id: int = Field(description="ID of the tenant")
    email: str = Field(description="User email")
    first_name: str = Field(description="First name")
    last_name: str = Field(description="Last name")
    role: str = Field(default="user", description="User role")
    is_active: bool = Field(default=True, description="Whether user is active")


class UpdateTenantUserArgs(BaseModel):
    tenant_id: int = Field(description="ID of the tenant")
    user_id: int = Field(description="ID of the user to update")
    email: Optional[str] = Field(default=None, description="User email")
    first_name: Optional[str] = Field(default=None, description="First name")
    last_name: Optional[str] = Field(default=None, description="Last name")
    role: Optional[str] = Field(default=None, description="User role")
    is_active: Optional[bool] = Field(default=None, description="Whether user is active")


class PromoteUserToAdminArgs(BaseModel):
    email: str = Field(description="Email of the user to promote")


class ResetUserPasswordArgs(BaseModel):
    user_id: int = Field(description="ID of the user")
    new_password: str = Field(description="New password")
    confirm_password: str = Field(description="Confirm new password")
    force_reset_on_login: bool = Field(default=False, description="Force password reset on login")


class ExportTenantDataArgs(BaseModel):
    tenant_id: int = Field(description="ID of the tenant to export")
    include_attachments: bool = Field(default=False, description="Include attachments in export")


class ImportTenantDataArgs(BaseModel):
    tenant_id: int = Field(description="ID of the tenant to import into")
    data: Dict[str, Any] = Field(description="Data to import")


# Tool argument schemas will be used directly with FastMCP decorators


class InvoiceTools:
    """Implementation of MCP tools for the Invoice Application"""
    
    def __init__(self, api_client: InvoiceAPIClient):
        self.api_client = api_client
    
    async def list_clients(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """List all clients"""
        try:
            clients = await self.api_client.list_clients(skip=skip, limit=limit)
            
            return {
                "success": True,
                "data": clients,
                "count": len(clients),
                "pagination": {
                    "skip": skip,
                    "limit": limit
                }
            }
            
        except AuthenticationError as e:
            logger.error(f"Authentication failed in list_clients: {e}")
            return {"success": False, "error": f"Authentication failed: {e}"}
        except Exception as e:
            logger.error(f"Failed to list clients: {e}")
            return {"success": False, "error": f"Failed to list clients: {e}"}
    
    async def search_clients(self, query: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Search for clients"""
        try:
            clients = await self.api_client.search_clients(
                query=query, 
                skip=skip, 
                limit=limit
            )
            
            return {
                "success": True,
                "data": clients,
                "count": len(clients),
                "search_query": query,
                "pagination": {
                    "skip": skip,
                    "limit": limit
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to search clients: {e}")
            return {"success": False, "error": f"Failed to search clients: {e}"}
    
    async def get_client(self, client_id: int) -> Dict[str, Any]:
        """Get a specific client"""
        try:
            client = await self.api_client.get_client(client_id)
            
            return {
                "success": True,
                "data": client
            }
            
        except Exception as e:
            logger.error(f"Failed to get client {client_id}: {e}")
            return {"success": False, "error": f"Failed to get client: {e}"}
    
    async def create_client(self, name: str, email: Optional[str] = None, phone: Optional[str] = None, address: Optional[str] = None) -> Dict[str, Any]:
        """Create a new client"""
        try:
            client_data = {"name": name}
            if email:
                client_data["email"] = email
            if phone:
                client_data["phone"] = phone
            if address:
                client_data["address"] = address
                
            client = await self.api_client.create_client(client_data)
            
            return {
                "success": True,
                "data": client,
                "message": "Client created successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to create client {name}: {e}")
            return {"success": False, "error": f"Failed to create client: {e}"}
    
    async def list_invoices(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """List all invoices"""
        try:
            invoices = await self.api_client.list_invoices(skip=skip, limit=limit)
            
            return {
                "success": True,
                "data": invoices,
                "count": len(invoices),
                "pagination": {
                    "skip": skip,
                    "limit": limit
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list invoices: {e}"}
    
    async def search_invoices(self, query: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Search for invoices"""
        try:
            invoices = await self.api_client.search_invoices(
                query=query,
                skip=skip,
                limit=limit
            )
            
            return {
                "success": True,
                "data": invoices,
                "count": len(invoices),
                "search_query": query,
                "pagination": {
                    "skip": skip,
                    "limit": limit
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to search invoices: {e}"}
    
    async def get_invoice(self, invoice_id: int) -> Dict[str, Any]:
        """Get a specific invoice"""
        try:
            invoice = await self.api_client.get_invoice(invoice_id)
            
            return {
                "success": True,
                "data": invoice
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get invoice: {e}"}
    
    async def create_invoice(self, client_id: int, amount: float, due_date: str, status: str = "draft", notes: Optional[str] = None) -> Dict[str, Any]:
        """Create a new invoice"""
        try:
            invoice_data = {
                "client_id": client_id,
                "amount": amount,
                "due_date": due_date,
                "status": status
            }
            if notes:
                invoice_data["notes"] = notes
                
            invoice = await self.api_client.create_invoice(invoice_data)
            
            return {
                "success": True,
                "data": invoice,
                "message": "Invoice created successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to create invoice: {e}"}

    # Expenses
    async def list_expenses(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        invoice_id: Optional[int] = None,
        unlinked_only: bool = False,
    ) -> Dict[str, Any]:
        try:
            expenses = await self.api_client.list_expenses(
                skip=skip,
                limit=limit,
                category=category,
                invoice_id=invoice_id,
                unlinked_only=unlinked_only,
            )
            return {
                "success": True,
                "data": expenses,
                "count": len(expenses),
                "pagination": {"skip": skip, "limit": limit},
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to list expenses: {e}"}

    async def get_expense(self, expense_id: int) -> Dict[str, Any]:
        try:
            expense = await self.api_client.get_expense(expense_id)
            return {"success": True, "data": expense}
        except Exception as e:
            return {"success": False, "error": f"Failed to get expense: {e}"}

    async def create_expense(
        self,
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
    ) -> Dict[str, Any]:
        try:
            payload: Dict[str, Any] = {
                "amount": amount,
                "currency": currency,
                "expense_date": expense_date,
                "category": category,
                "status": status or "recorded",
            }
            if vendor is not None:
                payload["vendor"] = vendor
            if tax_rate is not None:
                payload["tax_rate"] = tax_rate
            if tax_amount is not None:
                payload["tax_amount"] = tax_amount
            if total_amount is not None:
                payload["total_amount"] = total_amount
            if payment_method is not None:
                payload["payment_method"] = payment_method
            if reference_number is not None:
                payload["reference_number"] = reference_number
            if notes is not None:
                payload["notes"] = notes
            if invoice_id is not None:
                payload["invoice_id"] = invoice_id

            expense = await self.api_client.create_expense(payload)
            return {"success": True, "data": expense, "message": "Expense created successfully"}
        except Exception as e:
            return {"success": False, "error": f"Failed to create expense: {e}"}

    async def update_expense(
        self,
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
    ) -> Dict[str, Any]:
        try:
            payload: Dict[str, Any] = {}
            if amount is not None:
                payload["amount"] = amount
            if currency is not None:
                payload["currency"] = currency
            if expense_date is not None:
                payload["expense_date"] = expense_date
            if category is not None:
                payload["category"] = category
            if vendor is not None:
                payload["vendor"] = vendor
            if tax_rate is not None:
                payload["tax_rate"] = tax_rate
            if tax_amount is not None:
                payload["tax_amount"] = tax_amount
            if total_amount is not None:
                payload["total_amount"] = total_amount
            if payment_method is not None:
                payload["payment_method"] = payment_method
            if reference_number is not None:
                payload["reference_number"] = reference_number
            if status is not None:
                payload["status"] = status
            if notes is not None:
                payload["notes"] = notes
            if invoice_id is not None:
                payload["invoice_id"] = invoice_id

            expense = await self.api_client.update_expense(expense_id, payload)
            return {"success": True, "data": expense, "message": "Expense updated successfully"}
        except Exception as e:
            return {"success": False, "error": f"Failed to update expense: {e}"}

    async def delete_expense(self, expense_id: int) -> Dict[str, Any]:
        try:
            ok = await self.api_client.delete_expense(expense_id)
            if not ok:
                return {"success": False, "error": "Failed to delete expense"}
            return {"success": True, "message": "Expense deleted"}
        except Exception as e:
            return {"success": False, "error": f"Failed to delete expense: {e}"}

    async def upload_expense_receipt(
        self, expense_id: int, file_path: str, filename: Optional[str] = None, content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            result = await self.api_client.upload_expense_receipt(
                expense_id=expense_id,
                file_path=file_path,
                filename=filename,
                content_type=content_type,
            )
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": f"Failed to upload expense receipt: {e}"}

    async def list_expense_attachments(self, expense_id: int) -> Dict[str, Any]:
        try:
            items = await self.api_client.list_expense_attachments(expense_id)
            return {"success": True, "data": items, "count": len(items)}
        except Exception as e:
            return {"success": False, "error": f"Failed to list expense attachments: {e}"}

    async def delete_expense_attachment(self, expense_id: int, attachment_id: int) -> Dict[str, Any]:
        try:
            ok = await self.api_client.delete_expense_attachment(expense_id, attachment_id)
            if not ok:
                return {"success": False, "error": "Failed to delete expense attachment"}
            return {"success": True, "message": "Expense attachment deleted"}
        except Exception as e:
            return {"success": False, "error": f"Failed to delete expense attachment: {e}"}
    
    # Statement Management
    async def list_statements(self) -> Dict[str, Any]:
        """List all statements"""
        try:
            statements = await self.api_client.list_statements()
            return {
                "success": True,
                "data": statements.get("statements", []),
                "count": len(statements.get("statements", []))
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to list bank statements: {e}"}
    
    async def get_bank_statement(self, statement_id: int) -> Dict[str, Any]:
        """Get a specific bank statement with transactions"""
        try:
            statement = await self.api_client.get_bank_statement(statement_id)
            return {"success": True, "data": statement.get("statement", {})}
        except Exception as e:
            return {"success": False, "error": f"Failed to get bank statement: {e}"}
    
    async def reprocess_bank_statement(self, statement_id: int) -> Dict[str, Any]:
        """Reprocess a bank statement"""
        try:
            result = await self.api_client.reprocess_bank_statement(statement_id)
            return {"success": True, "data": result, "message": "Bank statement reprocessing started"}
        except Exception as e:
            return {"success": False, "error": f"Failed to reprocess bank statement: {e}"}
    
    async def update_bank_statement_meta(self, statement_id: int, notes: Optional[str] = None, labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update bank statement metadata"""
        try:
            meta_data = {}
            if notes is not None:
                meta_data["notes"] = notes
            if labels is not None:
                meta_data["labels"] = labels
            
            result = await self.api_client.update_bank_statement_meta(statement_id, meta_data)
            return {"success": True, "data": result.get("statement", {}), "message": "Bank statement updated"}
        except Exception as e:
            return {"success": False, "error": f"Failed to update bank statement: {e}"}
    
    async def delete_bank_statement(self, statement_id: int) -> Dict[str, Any]:
        """Delete a bank statement"""
        try:
            ok = await self.api_client.delete_bank_statement(statement_id)
            if not ok:
                return {"success": False, "error": "Failed to delete bank statement"}
            return {"success": True, "message": "Bank statement deleted"}
        except Exception as e:
            return {"success": False, "error": f"Failed to delete bank statement: {e}"}
    
    # Currency Management
    async def list_currencies(self, active_only: bool = True) -> Dict[str, Any]:
        """List supported currencies"""
        try:
            currencies = await self.api_client.list_currencies(active_only=active_only)
            
            return {
                "success": True,
                "data": currencies,
                "count": len(currencies),
                "active_only": active_only
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list currencies: {e}"}
    
    async def create_currency(self, code: str, name: str, symbol: str, decimal_places: int = 2, is_active: bool = True) -> Dict[str, Any]:
        """Create a custom currency"""
        try:
            currency_data = {
                "code": code.upper(),
                "name": name,
                "symbol": symbol,
                "decimal_places": decimal_places,
                "is_active": is_active
            }
            
            currency = await self.api_client.create_currency(currency_data)
            
            return {
                "success": True,
                "data": currency,
                "message": "Currency created successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to create currency: {e}"}
    
    async def convert_currency(self, amount: float, from_currency: str, to_currency: str, conversion_date: Optional[str] = None) -> Dict[str, Any]:
        """Convert amount from one currency to another"""
        try:
            conversion = await self.api_client.convert_currency(
                amount=amount,
                from_currency=from_currency,
                to_currency=to_currency,
                conversion_date=conversion_date
            )
            
            return {
                "success": True,
                "data": conversion
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to convert currency: {e}"}
    
    # Payments
    async def list_payments(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """List all payments"""
        try:
            payments = await self.api_client.list_payments(skip=skip, limit=limit)
            
            # Prepare chart data for smaller datasets only
            chart_data = None
            if len(payments) <= 500:  # Only generate charts for reasonable dataset sizes
                chart_data = self._prepare_payment_chart_data(payments)
            
            return {
                "success": True,
                "data": payments,
                "count": len(payments),
                "pagination": {
                    "skip": skip,
                    "limit": limit
                },
                "chart_data": chart_data
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list payments: {e}"}
    
    def _prepare_payment_chart_data(self, payments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare payment data for charts"""
        try:
            from datetime import datetime
            from collections import defaultdict
            
            # Group payments by date for timeline chart
            payments_by_date = defaultdict(float)
            payments_by_method = defaultdict(float)
            payments_by_invoice = defaultdict(list)
            
            for payment in payments:
                # Date grouping
                if payment.get('payment_date'):
                    try:
                        payment_date = datetime.fromisoformat(str(payment['payment_date'])).strftime('%Y-%m-%d')
                        payments_by_date[payment_date] += float(payment.get('amount', 0))
                    except:
                        pass
                
                # Payment method grouping
                method = payment.get('payment_method', 'unknown')
                payments_by_method[method] += float(payment.get('amount', 0))
                
                # Invoice grouping
                invoice_id = payment.get('invoice_id')
                if invoice_id:
                    payments_by_invoice[invoice_id].append({
                        'id': payment.get('id'),
                        'amount': payment.get('amount'),
                        'date': payment.get('payment_date'),
                        'method': payment.get('payment_method')
                    })
            
            # Prepare chart datasets
            timeline_data = [
                {'date': date, 'amount': amount} 
                for date, amount in sorted(payments_by_date.items())
            ]
            
            method_data = [
                {'method': method, 'amount': amount} 
                for method, amount in payments_by_method.items()
            ]
            
            # Calculate summary stats
            total_amount = sum(float(payment.get('amount', 0)) for payment in payments)
            avg_amount = total_amount / len(payments) if payments else 0
            
            return {
                'timeline': timeline_data,
                'by_method': method_data,
                'summary': {
                    'total_amount': total_amount,
                    'total_payments': len(payments),
                    'average_amount': avg_amount,
                    'date_range': {
                        'earliest': min(payments_by_date.keys()) if payments_by_date else None,
                        'latest': max(payments_by_date.keys()) if payments_by_date else None
                    }
                }
            }
            
        except Exception as e:
            return {'error': f'Failed to prepare chart data: {e}'}
    
    def _parse_date_filter(self, query_lower: str, payments: List[Dict[str, Any]]) -> Optional[tuple]:
        """Parse date-related keywords and filter payments accordingly"""
        from datetime import datetime, timedelta
        
        if "yesterday" in query_lower:
            yesterday = (datetime.now() - timedelta(days=1)).date()
            filtered = [p for p in payments if p.get('payment_date') and datetime.fromisoformat(str(p['payment_date'])).date() == yesterday]
            return filtered, True, "yesterday"
        elif "today" in query_lower:
            today = datetime.now().date()
            filtered = [p for p in payments if p.get('payment_date') and datetime.fromisoformat(str(p['payment_date'])).date() == today]
            return filtered, True, "today"
        elif "this week" in query_lower:
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            filtered = [p for p in payments if p.get('payment_date') and datetime.fromisoformat(str(p['payment_date'])) >= start_of_week]
            return filtered, True, "this week"
        elif "last week" in query_lower:
            today = datetime.now()
            start_of_this_week = today - timedelta(days=today.weekday())
            start_of_last_week = start_of_this_week - timedelta(days=7)
            end_of_last_week = start_of_this_week - timedelta(seconds=1)
            filtered = [p for p in payments if p.get('payment_date') and start_of_last_week <= datetime.fromisoformat(str(p['payment_date'])) <= end_of_last_week]
            return filtered, True, "last week"
        elif "this month" in query_lower:
            today = datetime.now()
            start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            filtered = [p for p in payments if p.get('payment_date') and datetime.fromisoformat(str(p['payment_date'])) >= start_of_month]
            return filtered, True, "this month"
        elif "last month" in query_lower:
            today = datetime.now()
            first_day_this_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if today.month == 1:
                first_day_last_month = first_day_this_month.replace(year=today.year-1, month=12)
            else:
                first_day_last_month = first_day_this_month.replace(month=today.month-1)
            last_day_last_month = first_day_this_month - timedelta(seconds=1)
            filtered = [p for p in payments if p.get('payment_date') and first_day_last_month <= datetime.fromisoformat(str(p['payment_date'])) <= last_day_last_month]
            return filtered, True, "last month"
        elif "past week" in query_lower:
            week_ago = datetime.now() - timedelta(days=7)
            filtered = [p for p in payments if p.get('payment_date') and datetime.fromisoformat(str(p['payment_date'])) >= week_ago]
            return filtered, True, "in the past 7 days"
        elif "past month" in query_lower:
            month_ago = datetime.now() - timedelta(days=30)
            filtered = [p for p in payments if p.get('payment_date') and datetime.fromisoformat(str(p['payment_date'])) >= month_ago]
            return filtered, True, "in the past 30 days"
        return None

    async def query_payments(self, query: str) -> Dict[str, Any]:
        """Query payments using natural language (e.g., 'payments yesterday', 'payments this week')"""
        try:
            from datetime import datetime, date, timedelta
            
            # Get all payments first
            payments = await self.api_client.list_payments(skip=0, limit=1000)
            
            # Parse the query for date-related keywords
            query_lower = query.lower()
            filtered_payments = payments
            date_filter_applied = False
            date_description = ""
            
            # Parse date-related keywords using helper method
            date_filter_result = self._parse_date_filter(query_lower, payments)
            if date_filter_result:
                filtered_payments, date_filter_applied, date_description = date_filter_result
            else:
                date_filter_applied = False
                date_description = ""

            
            # Parse payment method filters
            if "credit card" in query_lower or "card" in query_lower:
                filtered_payments = [
                    p for p in filtered_payments 
                    if p.get('payment_method') and 'credit' in p['payment_method'].lower()
                ]
            elif "cash" in query_lower:
                filtered_payments = [
                    p for p in filtered_payments 
                    if p.get('payment_method') and 'cash' in p['payment_method'].lower()
                ]
            elif "check" in query_lower or "cheque" in query_lower:
                filtered_payments = [
                    p for p in filtered_payments 
                    if p.get('payment_method') and 'check' in p['payment_method'].lower()
                ]
            
            # Parse amount filters
            if "over" in query_lower or "above" in query_lower:
                import re
                amount_match = re.search(r'(?:over|above)\s*\$?(\d+(?:\.\d+)?)', query_lower)
                if amount_match:
                    min_amount = float(amount_match.group(1))
                    filtered_payments = [
                        p for p in filtered_payments 
                        if p.get('amount') and float(p['amount']) > min_amount
                    ]
            elif "under" in query_lower or "below" in query_lower:
                import re
                amount_match = re.search(r'(?:under|below)\s*\$?(\d+(?:\.\d+)?)', query_lower)
                if amount_match:
                    max_amount = float(amount_match.group(1))
                    filtered_payments = [
                        p for p in filtered_payments 
                        if p.get('amount') and float(p['amount']) < max_amount
                    ]
            
            # Parse client filters
            if "from" in query_lower and "client" in query_lower:
                # This is already handled by the existing filtering logic
                pass
            
            return {
                "success": True,
                "data": filtered_payments,
                "count": len(filtered_payments),
                "query": query,
                "date_filter_applied": date_filter_applied,
                "date_description": date_description,
                "total_payments_checked": len(payments)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to query payments: {e}"}
    
    async def create_payment(self, invoice_id: int, amount: float, payment_date: str, payment_method: str, reference: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """Create a new payment"""
        try:
            payment_data = {
                "invoice_id": invoice_id,
                "amount": amount,
                "payment_date": payment_date,
                "payment_method": payment_method
            }
            if reference:
                payment_data["reference"] = reference
            if notes:
                payment_data["notes"] = notes
                
            payment = await self.api_client.create_payment(payment_data)
            
            return {
                "success": True,
                "data": payment,
                "message": "Payment created successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to create payment: {e}"}
    
    # Settings
    async def get_settings(self) -> Dict[str, Any]:
        """Get tenant settings"""
        try:
            settings = await self.api_client.get_settings()
            
            return {
                "success": True,
                "data": settings
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get settings: {e}"}
    
    # Discount Rules
    async def list_discount_rules(self) -> Dict[str, Any]:
        """List all discount rules"""
        try:
            discount_rules = await self.api_client.list_discount_rules()
            
            return {
                "success": True,
                "data": discount_rules,
                "count": len(discount_rules)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list discount rules: {e}"}
    
    async def create_discount_rule(self, name: str, discount_type: str, discount_value: float, min_amount: Optional[float] = None, max_discount: Optional[float] = None, priority: int = 1, is_active: bool = True, currency: Optional[str] = None) -> Dict[str, Any]:
        """Create a new discount rule"""
        try:
            rule_data = {
                "name": name,
                "discount_type": discount_type,
                "discount_value": discount_value,
                "priority": priority,
                "is_active": is_active
            }
            if min_amount is not None:
                rule_data["min_amount"] = min_amount
            if max_discount is not None:
                rule_data["max_discount"] = max_discount
            if currency:
                rule_data["currency"] = currency
                
            discount_rule = await self.api_client.create_discount_rule(rule_data)
            
            return {
                "success": True,
                "data": discount_rule,
                "message": "Discount rule created successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to create discount rule: {e}"}
    
    # CRM
    async def create_client_note(self, client_id: int, title: str, content: str, note_type: str = "general") -> Dict[str, Any]:
        """Create a note for a client"""
        try:
            note_data = {
                "title": title,
                "content": content,
                "note_type": note_type
            }
            
            note = await self.api_client.create_client_note(client_id, note_data)
            
            return {
                "success": True,
                "data": note,
                "message": "Client note created successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to create client note: {e}"}
    
    # Email
    async def send_invoice_email(self, invoice_id: int, to_email: Optional[str] = None, to_name: Optional[str] = None, subject: Optional[str] = None, message: Optional[str] = None) -> Dict[str, Any]:
        """Send an invoice via email"""
        try:
            email_data = {"invoice_id": invoice_id}
            if to_email:
                email_data["to_email"] = to_email
            if to_name:
                email_data["to_name"] = to_name
            if subject:
                email_data["subject"] = subject
            if message:
                email_data["message"] = message
                
            result = await self.api_client.send_invoice_email(email_data)
            
            return {
                "success": True,
                "data": result,
                "message": "Invoice email sent successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to send invoice email: {e}"}
    
    async def test_email_configuration(self, test_email: str) -> Dict[str, Any]:
        """Test email configuration"""
        try:
            result = await self.api_client.test_email_configuration(test_email)
            
            return {
                "success": True,
                "data": result,
                "message": "Email test completed"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to test email configuration: {e}"}
    
    # Tenant
    async def get_tenant_info(self) -> Dict[str, Any]:
        """Get current tenant information"""
        try:
            tenant = await self.api_client.get_tenant_info()
            
            return {
                "success": True,
                "data": tenant
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get tenant info: {e}"}
    
    async def get_clients_with_outstanding_balance(self) -> Dict[str, Any]:
        """Get clients with outstanding balances"""
        try:
            clients = await self.api_client.get_clients_with_outstanding_balance()
            
            return {
                "success": True,
                "data": clients,
                "count": len(clients),
                "message": f"Found {len(clients)} clients with outstanding balances"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get clients with outstanding balance: {e}"}
    
    async def get_overdue_invoices(self) -> Dict[str, Any]:
        """Get overdue invoices"""
        try:
            invoices = await self.api_client.get_overdue_invoices()
            
            return {
                "success": True,
                "data": invoices,
                "count": len(invoices),
                "message": f"Found {len(invoices)} overdue invoices"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get overdue invoices: {e}"}
    
    async def get_invoice_stats(self) -> Dict[str, Any]:
        """Get invoice statistics"""
        try:
            stats = await self.api_client.get_invoice_stats()
            
            return {
                "success": True,
                "data": stats
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get invoice stats: {e}"}

    async def analyze_invoice_patterns(self) -> Dict[str, Any]:
        """Analyze invoice patterns to identify trends and provide recommendations."""
        try:
            # Fetch invoices and clients with pagination for better performance
            # Use smaller initial limit and expand if needed
            invoices = await self.api_client.list_invoices(limit=500)
            clients = await self.api_client.list_clients(limit=500)

            if not invoices:
                return {"success": True, "data": {"message": "No invoices found to analyze."}}

            # Create a client map for easy lookup
            client_map = {client['id']: client for client in clients}

            # Analysis variables
            total_invoices = len(invoices)
            paid_invoices = [inv for inv in invoices if inv['status'] == 'paid']
            unpaid_invoices = [inv for inv in invoices if inv['status'] != 'paid']
            overdue_invoices = [inv for inv in unpaid_invoices if inv.get('due_date') and inv['due_date'] < datetime.now().isoformat()]
            
            total_revenue = sum(inv['amount'] for inv in paid_invoices)
            outstanding_revenue = sum(inv['amount'] for inv in unpaid_invoices)

            # Client analysis
            client_payment_times = {}
            for inv in paid_invoices:
                if inv.get('paid_date') and inv.get('created_at'):
                    client_id = inv['client_id']
                    paid_date = datetime.fromisoformat(inv['paid_date'])
                    created_date = datetime.fromisoformat(inv['created_at'])
                    payment_time = (paid_date - created_date).days
                    
                    if client_id not in client_payment_times:
                        client_payment_times[client_id] = []
                    client_payment_times[client_id].append(payment_time)

            avg_payment_times = {
                client_map.get(cid, {}).get('name', f"Client {cid}"): sum(times) / len(times)
                for cid, times in client_payment_times.items()
            }

            fastest_paying_clients = sorted(avg_payment_times.items(), key=lambda item: item[1])[:3]
            slowest_paying_clients = sorted(avg_payment_times.items(), key=lambda item: item[1], reverse=True)[:3]

            # Recommendations
            recommendations = []
            if overdue_invoices:
                recommendations.append(f"You have {len(overdue_invoices)} overdue invoices. Consider sending reminders.")
            if slowest_paying_clients:
                slow_client_name = slowest_paying_clients[0][0]
                recommendations.append(f"'{slow_client_name}' is your slowest paying client. Consider shortening their payment terms.")

            analysis_data = {
                "total_invoices": total_invoices,
                "paid_invoices": len(paid_invoices),
                "unpaid_invoices": len(unpaid_invoices),
                "overdue_invoices": len(overdue_invoices),
                "total_revenue": total_revenue,
                "outstanding_revenue": outstanding_revenue,
                "average_payment_time_days": sum(avg_payment_times.values()) / len(avg_payment_times) if avg_payment_times else 0,
                "fastest_paying_clients": fastest_paying_clients,
                "slowest_paying_clients": slowest_paying_clients,
                "recommendations": recommendations
            }

            return {"success": True, "data": analysis_data}

        except Exception as e:
            return {"success": False, "error": f"Failed to analyze invoice patterns: {e}"}

    async def suggest_invoice_actions(self) -> Dict[str, Any]:
        """Suggest actionable items based on invoice analysis."""
        try:
            analysis_result = await self.analyze_invoice_patterns()
            if not analysis_result.get("success"):
                return analysis_result

            analysis_data = analysis_result.get("data", {})
            recommendations = analysis_data.get("recommendations", [])
            overdue_invoices_count = analysis_data.get("overdue_invoices", 0)

            actions = []
            if overdue_invoices_count > 0:
                actions.append({
                    "action": "send_reminders",
                    "description": f"You have {overdue_invoices_count} overdue invoices. Would you like to draft reminder emails?",
                    "tool_to_use": "draft_reminder_email(invoice_id)"
                })
            
            if analysis_data.get("slowest_paying_clients"):
                slow_client = analysis_data["slowest_paying_clients"][0]
                actions.append({
                    "action": "review_payment_terms",
                    "description": f"'{slow_client[0]}' is your slowest paying client (avg. {slow_client[1]:.1f} days). Consider shortening their payment terms.",
                    "client_name": slow_client[0]
                })

            if not actions:
                actions.append({"action": "no_suggestions", "description": "Everything looks good! No immediate actions suggested."})

            return {"success": True, "data": {"suggested_actions": actions, "raw_analysis": analysis_data}}

        except Exception as e:
            return {"success": False, "error": f"Failed to suggest invoice actions: {e}"}

    # AI Configuration Tools
    async def list_ai_configs(self) -> Dict[str, Any]:
        """List all AI configurations"""
        try:
            configs = await self.api_client.list_ai_configs()
            return {
                "success": True,
                "data": configs,
                "count": len(configs),
                "message": f"Found {len(configs)} AI configurations"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to list AI configs: {e}"}

    async def create_ai_config(
        self,
        provider_name: str,
        model_name: str,
        provider_url: Optional[str] = None,
        api_key: Optional[str] = None,
        is_active: bool = True,
        is_default: bool = False,
        ocr_enabled: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """Create a new AI configuration"""
        try:
            config_data = {
                "provider_name": provider_name,
                "model_name": model_name,
                "is_active": is_active,
                "is_default": is_default,
                "ocr_enabled": ocr_enabled,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            if provider_url:
                config_data["provider_url"] = provider_url
            if api_key:
                config_data["api_key"] = api_key

            config = await self.api_client.create_ai_config(config_data)
            return {
                "success": True,
                "data": config,
                "message": "AI configuration created successfully"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to create AI config: {e}"}

    async def update_ai_config(
        self,
        config_id: int,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        provider_url: Optional[str] = None,
        api_key: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_default: Optional[bool] = None,
        ocr_enabled: Optional[bool] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Update an AI configuration"""
        try:
            update_data = {}
            if provider_name is not None:
                update_data["provider_name"] = provider_name
            if model_name is not None:
                update_data["model_name"] = model_name
            if provider_url is not None:
                update_data["provider_url"] = provider_url
            if api_key is not None:
                update_data["api_key"] = api_key
            if is_active is not None:
                update_data["is_active"] = is_active
            if is_default is not None:
                update_data["is_default"] = is_default
            if ocr_enabled is not None:
                update_data["ocr_enabled"] = ocr_enabled
            if max_tokens is not None:
                update_data["max_tokens"] = max_tokens
            if temperature is not None:
                update_data["temperature"] = temperature

            config = await self.api_client.update_ai_config(config_id, update_data)
            return {
                "success": True,
                "data": config,
                "message": "AI configuration updated successfully"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to update AI config: {e}"}

    async def test_ai_config(self, config_id: int, custom_prompt: Optional[str] = None, test_text: Optional[str] = None) -> Dict[str, Any]:
        """Test an AI configuration"""
        try:
            test_data = {}
            if custom_prompt:
                test_data["custom_prompt"] = custom_prompt
            if test_text:
                test_data["test_text"] = test_text

            result = await self.api_client.test_ai_config(config_id, test_data)
            return {
                "success": True,
                "data": result,
                "message": "AI configuration test completed"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to test AI config: {e}"}

    # Analytics Tools
    async def get_page_views_analytics(self, days: int = 7, path_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get page view analytics"""
        try:
            analytics = await self.api_client.get_page_views_analytics(days=days, path_filter=path_filter)
            return {
                "success": True,
                "data": analytics,
                "message": f"Analytics for the past {days} days"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get analytics: {e}"}

    # Audit Log Tools
    async def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get audit logs with optional filters"""
        try:
            logs = await self.api_client.get_audit_logs(
                user_id=user_id,
                user_email=user_email,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                status=status,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset
            )
            return {
                "success": True,
                "data": logs,
                "message": f"Found audit logs"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get audit logs: {e}"}

    # Notification Tools
    async def get_notification_settings(self) -> Dict[str, Any]:
        """Get current user's notification settings"""
        try:
            settings = await self.api_client.get_notification_settings()
            return {
                "success": True,
                "data": settings,
                "message": "Notification settings retrieved"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get notification settings: {e}"}

    async def update_notification_settings(
        self,
        invoice_created: bool = True,
        invoice_paid: bool = True,
        payment_received: bool = True,
        client_created: bool = False,
        overdue_invoice: bool = True,
        email_enabled: bool = True
    ) -> Dict[str, Any]:
        """Update current user's notification settings"""
        try:
            settings_data = {
                "invoice_created": invoice_created,
                "invoice_paid": invoice_paid,
                "payment_received": payment_received,
                "client_created": client_created,
                "overdue_invoice": overdue_invoice,
                "email_enabled": email_enabled
            }

            settings = await self.api_client.update_notification_settings(settings_data)
            return {
                "success": True,
                "data": settings,
                "message": "Notification settings updated successfully"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to update notification settings: {e}"}

    # PDF Processing Tools
    async def get_ai_status(self) -> Dict[str, Any]:
        """Get AI status for PDF processing"""
        try:
            status = await self.api_client.get_ai_status()
            return {
                "success": True,
                "data": status,
                "message": "AI status retrieved"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get AI status: {e}"}

    async def process_pdf_upload(self, file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Upload and process a PDF file"""
        try:
            result = await self.api_client.process_pdf_upload(file_path=file_path, filename=filename)
            return {
                "success": True,
                "data": result,
                "message": "PDF uploaded and processing started"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to process PDF upload: {e}"}

    # Tax Integration Tools
    async def get_tax_integration_status(self) -> Dict[str, Any]:
        """Get tax service integration status"""
        try:
            status = await self.api_client.get_tax_integration_status()
            return {
                "success": True,
                "data": status,
                "message": "Tax integration status retrieved"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get tax integration status: {e}"}

    async def send_to_tax_service(self, item_id: int, item_type: str) -> Dict[str, Any]:
        """Send item to tax service"""
        try:
            result = await self.api_client.send_to_tax_service(item_id=item_id, item_type=item_type)
            return {
                "success": True,
                "data": result,
                "message": f"Item {item_id} sent to tax service"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to send item to tax service: {e}"}

    async def bulk_send_to_tax_service(self, item_ids: List[int], item_type: str) -> Dict[str, Any]:
        """Bulk send items to tax service"""
        try:
            result = await self.api_client.bulk_send_to_tax_service(item_ids=item_ids, item_type=item_type)
            return {
                "success": True,
                "data": result,
                "message": f"Bulk sent {len(item_ids)} items to tax service"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to bulk send items to tax service: {e}"}

    async def get_tax_service_transactions(self) -> Dict[str, Any]:
        """Get tax service transactions"""
        try:
            transactions = await self.api_client.get_tax_service_transactions()
            return {
                "success": True,
                "data": transactions,
                "count": len(transactions),
                "message": f"Found {len(transactions)} tax service transactions"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get tax service transactions: {e}"}

    # Super Admin Tools
    async def get_tenant_stats(self, tenant_id: int) -> Dict[str, Any]:
        """Get detailed statistics for a specific tenant"""
        try:
            stats = await self.api_client.get_tenant_stats(tenant_id)
            return {
                "success": True,
                "data": stats,
                "message": f"Retrieved stats for tenant {tenant_id}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get tenant stats: {e}"}

    async def create_tenant(
        self,
        name: str,
        domain: str,
        company_name: Optional[str] = None,
        logo_url: Optional[str] = None,
        is_active: bool = True,
        max_users: Optional[int] = None,
        subscription_plan: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new tenant"""
        try:
            tenant_data = {
                "name": name,
                "domain": domain,
                "is_active": is_active
            }
            if company_name:
                tenant_data["company_name"] = company_name
            if logo_url:
                tenant_data["logo_url"] = logo_url
            if max_users is not None:
                tenant_data["max_users"] = max_users
            if subscription_plan:
                tenant_data["subscription_plan"] = subscription_plan

            tenant = await self.api_client.create_tenant(tenant_data)
            return {
                "success": True,
                "data": tenant,
                "message": "Tenant created successfully"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to create tenant: {e}"}

    async def update_tenant(
        self,
        tenant_id: int,
        name: Optional[str] = None,
        domain: Optional[str] = None,
        company_name: Optional[str] = None,
        logo_url: Optional[str] = None,
        is_active: Optional[bool] = None,
        max_users: Optional[int] = None,
        subscription_plan: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update tenant information"""
        try:
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if domain is not None:
                update_data["domain"] = domain
            if company_name is not None:
                update_data["company_name"] = company_name
            if logo_url is not None:
                update_data["logo_url"] = logo_url
            if is_active is not None:
                update_data["is_active"] = is_active
            if max_users is not None:
                update_data["max_users"] = max_users
            if subscription_plan is not None:
                update_data["subscription_plan"] = subscription_plan

            tenant = await self.api_client.update_tenant(tenant_id, update_data)
            return {
                "success": True,
                "data": tenant,
                "message": f"Tenant {tenant_id} updated successfully"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to update tenant: {e}"}

    async def delete_tenant(self, tenant_id: int) -> Dict[str, Any]:
        """Delete a tenant"""
        try:
            success = await self.api_client.delete_tenant(tenant_id)
            if success:
                return {
                    "success": True,
                    "message": f"Tenant {tenant_id} deleted successfully"
                }
            else:
                return {"success": False, "error": "Failed to delete tenant"}
        except Exception as e:
            return {"success": False, "error": f"Failed to delete tenant: {e}"}

    async def list_tenant_users(self, tenant_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """List users in a specific tenant"""
        try:
            users = await self.api_client.list_tenant_users(tenant_id, skip=skip, limit=limit)
            return {
                "success": True,
                "data": users,
                "count": len(users),
                "pagination": {"skip": skip, "limit": limit},
                "message": f"Found {len(users)} users in tenant {tenant_id}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to list tenant users: {e}"}

    async def create_tenant_user(
        self,
        tenant_id: int,
        email: str,
        first_name: str,
        last_name: str,
        role: str = "user",
        is_active: bool = True
    ) -> Dict[str, Any]:
        """Create a user in a specific tenant"""
        try:
            user_data = {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "is_active": is_active
            }

            user = await self.api_client.create_tenant_user(tenant_id, user_data)
            return {
                "success": True,
                "data": user,
                "message": f"User created successfully in tenant {tenant_id}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to create tenant user: {e}"}

    async def update_tenant_user(
        self,
        tenant_id: int,
        user_id: int,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update a user in a specific tenant"""
        try:
            update_data = {}
            if email is not None:
                update_data["email"] = email
            if first_name is not None:
                update_data["first_name"] = first_name
            if last_name is not None:
                update_data["last_name"] = last_name
            if role is not None:
                update_data["role"] = role
            if is_active is not None:
                update_data["is_active"] = is_active

            user = await self.api_client.update_tenant_user(tenant_id, user_id, update_data)
            return {
                "success": True,
                "data": user,
                "message": f"User {user_id} updated successfully in tenant {tenant_id}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to update tenant user: {e}"}

    async def delete_tenant_user(self, tenant_id: int, user_id: int) -> Dict[str, Any]:
        """Delete a user from a specific tenant"""
        try:
            success = await self.api_client.delete_tenant_user(tenant_id, user_id)
            if success:
                return {
                    "success": True,
                    "message": f"User {user_id} deleted successfully from tenant {tenant_id}"
                }
            else:
                return {"success": False, "error": "Failed to delete tenant user"}
        except Exception as e:
            return {"success": False, "error": f"Failed to delete tenant user: {e}"}

    async def promote_user_to_admin(self, email: str) -> Dict[str, Any]:
        """Promote a user to admin"""
        try:
            result = await self.api_client.promote_user_to_admin(email)
            return {
                "success": True,
                "data": result,
                "message": f"User {email} promoted to admin successfully"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to promote user to admin: {e}"}

    async def reset_user_password(self, user_id: int, new_password: str, confirm_password: str, force_reset_on_login: bool = False) -> Dict[str, Any]:
        """Reset a user's password"""
        try:
            result = await self.api_client.reset_user_password(user_id, new_password, confirm_password, force_reset_on_login)
            return {
                "success": True,
                "data": result,
                "message": f"Password reset successfully for user {user_id}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to reset user password: {e}"}

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        try:
            stats = await self.api_client.get_system_stats()
            return {
                "success": True,
                "data": stats,
                "message": "System statistics retrieved"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get system stats: {e}"}

    async def export_tenant_data(self, tenant_id: int, include_attachments: bool = False) -> Dict[str, Any]:
        """Export tenant data"""
        try:
            result = await self.api_client.export_tenant_data(tenant_id, include_attachments)
            return {
                "success": True,
                "data": result,
                "message": f"Tenant {tenant_id} data exported successfully"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to export tenant data: {e}"}

    async def import_tenant_data(self, tenant_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Import data into a tenant"""
        try:
            result = await self.api_client.import_tenant_data(tenant_id, data)
            return {
                "success": True,
                "data": result,
                "message": f"Data imported successfully into tenant {tenant_id}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to import tenant data: {e}"} 