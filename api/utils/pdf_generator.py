from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from typing import Dict, Any, List
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class InvoicePDFGenerator:
    """Generate PDF invoices using ReportLab"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            alignment=TA_LEFT,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='RightAlign',
            parent=self.styles['Normal'],
            alignment=TA_RIGHT
        ))
    
    def generate_invoice_pdf(
        self,
        invoice_data: Dict[str, Any],
        client_data: Dict[str, Any],
        company_data: Dict[str, Any],
        items: List[Dict[str, Any]] = None
    ) -> bytes:
        """Generate a PDF invoice and return as bytes"""
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build document content
            story = []
            
            # Header
            story.extend(self._build_header(company_data))
            story.append(Spacer(1, 20))
            
            # Invoice title and details
            story.extend(self._build_invoice_details(invoice_data))
            story.append(Spacer(1, 20))
            
            # Client information
            story.extend(self._build_client_info(client_data))
            story.append(Spacer(1, 20))
            
            # Invoice items table
            if items:
                story.extend(self._build_items_table(items))
            else:
                # Create a simple items table if no items provided
                story.extend(self._build_simple_total(invoice_data))
            
            story.append(Spacer(1, 20))
            
            # Total and payment info
            story.extend(self._build_totals(invoice_data))
            story.append(Spacer(1, 30))
            
            # Notes
            if invoice_data.get('notes'):
                story.extend(self._build_notes(invoice_data['notes']))
            
            # Footer
            story.extend(self._build_footer(company_data))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated PDF for invoice {invoice_data.get('number', 'draft')}")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {str(e)}")
            raise
    
    def _build_header(self, company_data: Dict[str, Any]) -> List:
        """Build company header section"""
        elements = []
        
        # Company name
        company_name = company_data.get('name', 'Your Company')
        elements.append(Paragraph(company_name, self.styles['CompanyName']))
        
        # Company details
        company_info = []
        if company_data.get('address'):
            company_info.append(company_data['address'])
        if company_data.get('phone'):
            company_info.append(f"Phone: {company_data['phone']}")
        if company_data.get('email'):
            company_info.append(f"Email: {company_data['email']}")
        if company_data.get('tax_id'):
            company_info.append(f"Tax ID: {company_data['tax_id']}")
        
        if company_info:
            elements.append(Paragraph('<br/>'.join(company_info), self.styles['Normal']))
        
        return elements
    
    def _build_invoice_details(self, invoice_data: Dict[str, Any]) -> List:
        """Build invoice details section"""
        elements = []
        
        # Invoice title
        elements.append(Paragraph("INVOICE", self.styles['InvoiceTitle']))
        
        # Invoice details table
        details_data = [
            ['Invoice Number:', invoice_data.get('number', 'Draft')],
            ['Invoice Date:', self._format_date(invoice_data.get('date'))],
            ['Due Date:', self._format_date(invoice_data.get('due_date'))],
            ['Status:', invoice_data.get('status', 'Draft').title()],
        ]
        
        details_table = Table(details_data, colWidths=[2*inch, 3*inch])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(details_table)
        
        return elements
    
    def _build_client_info(self, client_data: Dict[str, Any]) -> List:
        """Build client information section"""
        elements = []
        
        elements.append(Paragraph("Bill To:", self.styles['SectionHeader']))
        
        client_info = [client_data.get('name', 'Client Name')]
        if client_data.get('email'):
            client_info.append(client_data['email'])
        if client_data.get('phone'):
            client_info.append(client_data['phone'])
        if client_data.get('address'):
            client_info.append(client_data['address'])
        
        elements.append(Paragraph('<br/>'.join(client_info), self.styles['Normal']))
        
        return elements
    
    def _build_items_table(self, items: List[Dict[str, Any]]) -> List:
        """Build items table"""
        elements = []
        
        # Table header
        table_data = [['Description', 'Quantity', 'Price', 'Amount']]
        
        # Table rows
        for item in items:
            table_data.append([
                item.get('description', ''),
                str(item.get('quantity', 1)),
                f"${item.get('price', 0):.2f}",
                f"${item.get('amount', 0):.2f}"
            ])
        
        # Create table
        items_table = Table(table_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows styling
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(items_table)
        
        return elements
    
    def _build_simple_total(self, invoice_data: Dict[str, Any]) -> List:
        """Build simple total section when no items are provided"""
        elements = []
        
        # Simple service/total line
        table_data = [
            ['Description', 'Amount'],
            ['Services/Products', f"${invoice_data.get('amount', 0):.2f}"]
        ]
        
        simple_table = Table(table_data, colWidths=[4*inch, 2*inch])
        simple_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            ('ALIGN', (0, 1), (0, 1), 'LEFT'),
            ('ALIGN', (1, 1), (1, 1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(simple_table)
        
        return elements
    
    def _build_totals(self, invoice_data: Dict[str, Any]) -> List:
        """Build totals section"""
        elements = []
        
        amount = invoice_data.get('amount', 0)
        paid_amount = invoice_data.get('paid_amount', 0)
        balance_due = amount - paid_amount
        
        # Totals table
        totals_data = [
            ['Subtotal:', f"${amount:.2f}"],
        ]
        
        if paid_amount > 0:
            totals_data.append(['Paid Amount:', f"${paid_amount:.2f}"])
        
        totals_data.append(['Balance Due:', f"${balance_due:.2f}"])
        
        totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(totals_table)
        
        return elements
    
    def _build_notes(self, notes: str) -> List:
        """Build notes section"""
        elements = []
        
        elements.append(Paragraph("Notes:", self.styles['SectionHeader']))
        elements.append(Paragraph(notes, self.styles['Normal']))
        
        return elements
    
    def _build_footer(self, company_data: Dict[str, Any]) -> List:
        """Build footer section"""
        elements = []
        
        elements.append(Spacer(1, 30))
        
        footer_text = "Thank you for your business!"
        if company_data.get('name'):
            footer_text = f"Thank you for choosing {company_data['name']}!"
        
        elements.append(Paragraph(footer_text, self.styles['Normal']))
        
        return elements
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for display"""
        if not date_str:
            return ""
        
        try:
            # Try parsing ISO format first
            if 'T' in date_str:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            return date_obj.strftime('%B %d, %Y')
        except (ValueError, TypeError):
            return str(date_str)

def generate_invoice_pdf(
    invoice_data: Dict[str, Any],
    client_data: Dict[str, Any],
    company_data: Dict[str, Any],
    items: List[Dict[str, Any]] = None
) -> bytes:
    """Convenience function to generate invoice PDF"""
    generator = InvoicePDFGenerator()
    return generator.generate_invoice_pdf(invoice_data, client_data, company_data, items) 