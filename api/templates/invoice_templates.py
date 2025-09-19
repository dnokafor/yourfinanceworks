from typing import Dict, Any
from abc import ABC, abstractmethod
from reportlab.lib import colors

class InvoiceTemplate(ABC):
    """Base template class"""
    
    @abstractmethod
    def get_colors(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_layout(self) -> Dict[str, Any]:
        pass

class ModernTemplate(InvoiceTemplate):
    def get_colors(self) -> Dict[str, Any]:
        return {
            'title': colors.darkblue,
            'header': colors.darkblue,
            'accent': colors.lightblue,
        }
    
    def get_layout(self) -> Dict[str, Any]:
        return {
            'show_logo': True,
            'table_style': 'modern',
        }

class ClassicTemplate(InvoiceTemplate):
    def get_colors(self) -> Dict[str, Any]:
        return {
            'title': colors.black,
            'header': colors.black,
            'accent': colors.grey,
        }
    
    def get_layout(self) -> Dict[str, Any]:
        return {
            'show_logo': False,
            'table_style': 'classic',
        }

TEMPLATES = {
    'modern': ModernTemplate(),
    'classic': ClassicTemplate(),
}

def get_template(name: str = 'modern') -> InvoiceTemplate:
    return TEMPLATES.get(name, TEMPLATES['modern'])