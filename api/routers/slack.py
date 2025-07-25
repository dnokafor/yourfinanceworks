from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import json
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime, date
import asyncio

from MCP.api_client import InvoiceAPIClient
from MCP.tools import InvoiceTools

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/slack", tags=["slack"])

class SlackCommandParser:
    """Parse Slack commands into structured operations"""
    
    def __init__(self):
        self.patterns = {
            'create_client': [
                r'create client (?P<name>[^,]+)(?:,\s*email:\s*(?P<email>\S+))?(?:,\s*phone:\s*(?P<phone>[^,]+))?',
                r'add client (?P<name>[^,]+)(?:,\s*(?P<email>\S+))?'
            ],
            'create_invoice': [
                r'create invoice for (?P<client_name>[^,]+),?\s*amount:\s*(?P<amount>[\d.]+)(?:,\s*due:\s*(?P<due_date>[\d-]+))?',
                r'invoice (?P<client_name>[^,]+)\s+(?P<amount>[\d.]+)(?:\s+due\s+(?P<due_date>[\d-]+))?'
            ],
            'list_clients': [r'list clients?', r'show clients?'],
            'list_invoices': [r'list invoices?', r'show invoices?'],
            'search_client': [r'find client (?P<query>.+)', r'search client (?P<query>.+)'],
            'search_invoice': [r'find invoice (?P<query>.+)', r'search invoice (?P<query>.+)'],
            'overdue_invoices': [r'overdue invoices?', r'show overdue'],
            'outstanding_balance': [r'outstanding balance', r'who owes money'],
            'invoice_stats': [r'invoice stats', r'statistics', r'dashboard']
        }
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse Slack command text into structured operation"""
        text = text.strip().lower()
        
        for operation, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return {
                        'operation': operation,
                        'params': match.groupdict() if hasattr(match, 'groupdict') else {}
                    }
        
        return {'operation': 'unknown', 'params': {}, 'original_text': text}

class SlackInvoiceBot:
    """Main Slack bot for invoice operations"""
    
    def __init__(self):
        self.parser = SlackCommandParser()
        self.api_client = None
        self.tools = None
    
    async def initialize(self, api_url: str, email: str, password: str):
        """Initialize API client and tools"""
        self.api_client = InvoiceAPIClient(
            base_url=api_url,
            email=email,
            password=password
        )
        self.tools = InvoiceTools(self.api_client)
    
    async def process_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Slack command and return response"""
        if not self.tools:
            return self._error_response("Bot not initialized")
        
        parsed = self.parser.parse(command_data.get('text', ''))
        operation = parsed['operation']
        params = parsed['params']
        
        try:
            if operation == 'create_client':
                return await self._create_client(params)
            elif operation == 'create_invoice':
                return await self._create_invoice(params)
            elif operation == 'list_clients':
                return await self._list_clients()
            elif operation == 'list_invoices':
                return await self._list_invoices()
            elif operation == 'search_client':
                return await self._search_clients(params.get('query', ''))
            elif operation == 'search_invoice':
                return await self._search_invoices(params.get('query', ''))
            elif operation == 'overdue_invoices':
                return await self._get_overdue_invoices()
            elif operation == 'outstanding_balance':
                return await self._get_outstanding_balance()
            elif operation == 'invoice_stats':
                return await self._get_invoice_stats()
            else:
                return self._help_response()
        
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return self._error_response(f"Error: {str(e)}")
    
    async def _create_client(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new client"""
        name = params.get('name', '').strip()
        if not name:
            return self._error_response("Client name is required")
        
        result = await self.tools.create_client(
            name=name,
            email=params.get('email'),
            phone=params.get('phone')
        )
        
        if result.get('success'):
            client = result['data']
            return self._success_response(
                f"✅ Client created: *{client['name']}*\n"
                f"ID: {client['id']}\n" +
                (f"Email: {client['email']}\n" if client.get('email') else "") +
                (f"Phone: {client['phone']}\n" if client.get('phone') else "")
            )
        else:
            return self._error_response(result.get('error', 'Failed to create client'))
    
    async def _create_invoice(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new invoice"""
        client_name = params.get('client_name', '').strip()
        amount = params.get('amount')
        
        if not client_name or not amount:
            return self._error_response("Client name and amount are required")
        
        # Find client by name
        search_result = await self.tools.search_clients(client_name)
        if not search_result.get('success') or not search_result.get('data'):
            return self._error_response(f"Client '{client_name}' not found")
        
        client = search_result['data'][0]
        
        # Parse due date or use default (30 days from now)
        due_date = params.get('due_date')
        if not due_date:
            from datetime import datetime, timedelta
            due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        result = await self.tools.create_invoice(
            client_id=client['id'],
            amount=float(amount),
            due_date=due_date,
            status='draft'
        )
        
        if result.get('success'):
            invoice = result['data']
            return self._success_response(
                f"✅ Invoice created: *#{invoice['number']}*\n"
                f"Client: {client['name']}\n"
                f"Amount: ${invoice['amount']:.2f}\n"
                f"Due: {invoice['due_date']}\n"
                f"Status: {invoice['status']}"
            )
        else:
            return self._error_response(result.get('error', 'Failed to create invoice'))
    
    async def _list_clients(self) -> Dict[str, Any]:
        """List all clients"""
        result = await self.tools.list_clients(limit=10)
        
        if result.get('success'):
            clients = result['data']
            if not clients:
                return self._success_response("No clients found")
            
            text = "📋 *Clients:*\n"
            for client in clients[:10]:
                balance = client.get('outstanding_balance', 0)
                balance_text = f" (${balance:.2f})" if balance > 0 else ""
                text += f"• {client['name']}{balance_text}\n"
            
            if len(clients) > 10:
                text += f"\n... and {len(clients) - 10} more"
            
            return self._success_response(text)
        else:
            return self._error_response(result.get('error', 'Failed to list clients'))
    
    async def _list_invoices(self) -> Dict[str, Any]:
        """List recent invoices"""
        result = await self.tools.list_invoices(limit=10)
        
        if result.get('success'):
            invoices = result['data']
            if not invoices:
                return self._success_response("No invoices found")
            
            text = "📄 *Recent Invoices:*\n"
            for invoice in invoices[:10]:
                status_emoji = "✅" if invoice['status'] == 'paid' else "⏳"
                text += f"{status_emoji} #{invoice['number']} - {invoice.get('client_name', 'Unknown')} - ${invoice['amount']:.2f}\n"
            
            return self._success_response(text)
        else:
            return self._error_response(result.get('error', 'Failed to list invoices'))
    
    async def _search_clients(self, query: str) -> Dict[str, Any]:
        """Search for clients"""
        result = await self.tools.search_clients(query)
        
        if result.get('success'):
            clients = result['data']
            if not clients:
                return self._success_response(f"No clients found matching '{query}'")
            
            text = f"🔍 *Clients matching '{query}':*\n"
            for client in clients[:5]:
                text += f"• {client['name']}"
                if client.get('email'):
                    text += f" ({client['email']})"
                text += "\n"
            
            return self._success_response(text)
        else:
            return self._error_response(result.get('error', 'Failed to search clients'))
    
    async def _search_invoices(self, query: str) -> Dict[str, Any]:
        """Search for invoices"""
        result = await self.tools.search_invoices(query)
        
        if result.get('success'):
            invoices = result['data']
            if not invoices:
                return self._success_response(f"No invoices found matching '{query}'")
            
            text = f"🔍 *Invoices matching '{query}':*\n"
            for invoice in invoices[:5]:
                status_emoji = "✅" if invoice['status'] == 'paid' else "⏳"
                text += f"{status_emoji} #{invoice['number']} - ${invoice['amount']:.2f} ({invoice['status']})\n"
            
            return self._success_response(text)
        else:
            return self._error_response(result.get('error', 'Failed to search invoices'))
    
    async def _get_overdue_invoices(self) -> Dict[str, Any]:
        """Get overdue invoices"""
        result = await self.tools.get_overdue_invoices()
        
        if result.get('success'):
            invoices = result['data']
            if not invoices:
                return self._success_response("🎉 No overdue invoices!")
            
            text = f"⚠️ *{len(invoices)} Overdue Invoices:*\n"
            total_overdue = 0
            for invoice in invoices[:10]:
                text += f"• #{invoice['number']} - {invoice.get('client_name', 'Unknown')} - ${invoice['amount']:.2f}\n"
                total_overdue += invoice['amount']
            
            text += f"\n💰 Total overdue: ${total_overdue:.2f}"
            return self._success_response(text)
        else:
            return self._error_response(result.get('error', 'Failed to get overdue invoices'))
    
    async def _get_outstanding_balance(self) -> Dict[str, Any]:
        """Get clients with outstanding balance"""
        result = await self.tools.get_clients_with_outstanding_balance()
        
        if result.get('success'):
            clients = result['data']
            if not clients:
                return self._success_response("🎉 No outstanding balances!")
            
            text = f"💰 *Clients with Outstanding Balance:*\n"
            total_outstanding = 0
            for client in clients[:10]:
                balance = client.get('outstanding_balance', 0)
                text += f"• {client['name']}: ${balance:.2f}\n"
                total_outstanding += balance
            
            text += f"\n💰 Total outstanding: ${total_outstanding:.2f}"
            return self._success_response(text)
        else:
            return self._error_response(result.get('error', 'Failed to get outstanding balance'))
    
    async def _get_invoice_stats(self) -> Dict[str, Any]:
        """Get invoice statistics"""
        result = await self.tools.get_invoice_stats()
        
        if result.get('success'):
            stats = result['data']
            text = "📊 *Invoice Statistics:*\n"
            if 'total_income' in stats:
                text += f"💰 Total Income: ${stats['total_income']:.2f}\n"
            
            # Get additional stats
            invoices_result = await self.tools.list_invoices(limit=1000)
            if invoices_result.get('success'):
                invoices = invoices_result['data']
                paid_count = len([i for i in invoices if i['status'] == 'paid'])
                pending_count = len([i for i in invoices if i['status'] in ['pending', 'sent']])
                
                text += f"📄 Total Invoices: {len(invoices)}\n"
                text += f"✅ Paid: {paid_count}\n"
                text += f"⏳ Pending: {pending_count}\n"
            
            return self._success_response(text)
        else:
            return self._error_response(result.get('error', 'Failed to get invoice stats'))
    
    def _success_response(self, text: str) -> Dict[str, Any]:
        """Format success response for Slack"""
        return {
            "response_type": "in_channel",
            "text": text
        }
    
    def _error_response(self, error: str) -> Dict[str, Any]:
        """Format error response for Slack"""
        return {
            "response_type": "ephemeral",
            "text": f"❌ {error}"
        }
    
    def _help_response(self) -> Dict[str, Any]:
        """Show help message"""
        help_text = """
🤖 *Invoice Bot Commands:*

*Clients:*
• `create client John Doe, email: john@example.com`
• `list clients`
• `find client John`

*Invoices:*
• `create invoice for John Doe, amount: 500, due: 2024-02-15`
• `invoice John Doe 500 due 2024-02-15`
• `list invoices`
• `find invoice 123`

*Reports:*
• `overdue invoices`
• `outstanding balance`
• `invoice stats`
        """
        return self._success_response(help_text.strip())

# Global bot instance
bot = SlackInvoiceBot()

@router.post("/commands")
async def handle_slack_command(request: Request):
    """Handle Slack slash commands"""
    try:
        # Parse form data from Slack
        form_data = await request.form()
        command_data = {
            'token': form_data.get('token'),
            'team_id': form_data.get('team_id'),
            'team_domain': form_data.get('team_domain'),
            'channel_id': form_data.get('channel_id'),
            'channel_name': form_data.get('channel_name'),
            'user_id': form_data.get('user_id'),
            'user_name': form_data.get('user_name'),
            'command': form_data.get('command'),
            'text': form_data.get('text', ''),
            'response_url': form_data.get('response_url')
        }
        
        # Verify Slack token (you should set this in environment)
        import os
        expected_token = os.getenv('SLACK_VERIFICATION_TOKEN')
        if expected_token and command_data.get('token') != expected_token:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Initialize bot if not already done
        if not bot.api_client:
            api_url = os.getenv('INVOICE_API_BASE_URL', 'http://localhost:8000/api')
            email = os.getenv('SLACK_BOT_EMAIL')
            password = os.getenv('SLACK_BOT_PASSWORD')
            
            if not email or not password:
                return JSONResponse({
                    "response_type": "ephemeral",
                    "text": "❌ Bot not configured. Please set SLACK_BOT_EMAIL and SLACK_BOT_PASSWORD environment variables."
                })
            
            await bot.initialize(api_url, email, password)
        
        # Process command
        response = await bot.process_command(command_data)
        return JSONResponse(response)
        
    except Exception as e:
        logger.error(f"Error handling Slack command: {e}")
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"❌ Error processing command: {str(e)}"
        })

@router.post("/events")
async def handle_slack_events(request: Request):
    """Handle Slack Events API"""
    try:
        data = await request.json()
        
        # Handle URL verification challenge
        if data.get('type') == 'url_verification':
            return JSONResponse({"challenge": data.get('challenge')})
        
        # Handle app mentions and direct messages
        if data.get('type') == 'event_callback':
            event = data.get('event', {})
            
            if event.get('type') == 'app_mention' or event.get('type') == 'message':
                # Extract text and remove bot mention
                text = event.get('text', '')
                if text.startswith('<@'):
                    text = re.sub(r'<@[^>]+>\s*', '', text)
                
                # Process as command
                command_data = {
                    'text': text,
                    'user_id': event.get('user'),
                    'channel_id': event.get('channel')
                }
                
                # Initialize bot if needed
                if not bot.api_client:
                    api_url = os.getenv('INVOICE_API_BASE_URL', 'http://localhost:8000/api')
                    email = os.getenv('SLACK_BOT_EMAIL')
                    password = os.getenv('SLACK_BOT_PASSWORD')
                    
                    if email and password:
                        await bot.initialize(api_url, email, password)
                
                response = await bot.process_command(command_data)
                
                # Send response back to Slack (you'd need to implement this with Slack Web API)
                # For now, just return 200 OK
                return JSONResponse({"status": "ok"})
        
        return JSONResponse({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        return JSONResponse({"status": "error"})

@router.get("/health")
async def slack_health_check():
    """Health check for Slack integration"""
    return {
        "status": "healthy",
        "bot_initialized": bot.api_client is not None,
        "timestamp": datetime.now().isoformat()
    }