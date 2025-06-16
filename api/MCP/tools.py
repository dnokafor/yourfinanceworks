"""
FastMCP Tools for Invoice Application
"""
from typing import Any, Dict, List, Optional
import json
from pydantic import BaseModel, Field

from .api_client import InvoiceAPIClient
from .auth_client import AuthenticationError


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
            return {"success": False, "error": f"Authentication failed: {e}"}
        except Exception as e:
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