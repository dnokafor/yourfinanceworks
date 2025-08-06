from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import tempfile
import os
import subprocess
import sys
from typing import Dict, Any
import logging

from models.database import get_db
from models.models import User, Client
from auth import current_active_user

router = APIRouter(prefix="/invoices", tags=["pdf-processing"])
logger = logging.getLogger(__name__)

@router.post("/process-pdf")
async def process_pdf(
    pdf_file: UploadFile = File(...),
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Process PDF invoice and extract data using the main.py script"""
    
    if not pdf_file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await pdf_file.read()
            temp_file.write(content)
            temp_pdf_path = temp_file.name
        
        # Run the main.py script to process the PDF
        script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'main.py')
        
        try:
            # Run the PDF processing script
            result = subprocess.run([
                sys.executable, script_path, 
                '--pdf-path', temp_pdf_path,
                '--output-json'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error(f"PDF processing failed: {result.stderr}")
                raise HTTPException(status_code=500, detail="Failed to process PDF with LLM")
            
            # Parse the JSON output
            import json
            try:
                extracted_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON output: {result.stdout}")
                raise HTTPException(status_code=500, detail="Invalid response from PDF processor")
            
            # Check if client exists or needs to be created
            client_info = extracted_data.get('bills_to', '')
            existing_client = None
            
            if client_info:
                # Try to find existing client by name (simple matching)
                client_name = client_info.split('\n')[0].strip() if client_info else ''
                if client_name:
                    existing_client = db.query(Client).filter(
                        Client.name.ilike(f"%{client_name}%")
                    ).first()
            
            # Format response
            response_data = {
                'invoice_data': extracted_data,
                'client_exists': existing_client is not None,
                'existing_client': {
                    'id': existing_client.id,
                    'name': existing_client.name,
                    'email': existing_client.email
                } if existing_client else None,
                'suggested_client': {
                    'name': client_info.split('\n')[0].strip() if client_info else '',
                    'address': client_info
                } if client_info else None
            }
            
            return {
                'success': True,
                'data': response_data,
                'message': 'PDF processed successfully'
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="PDF processing timed out")
    except Exception as e:
        logger.error(f"Unexpected error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@router.get("/ai-status")
async def check_ai_status():
    """Check if AI/LLM is configured and available"""
    try:
        # Check if Ollama is running by trying to connect
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return {
                'configured': len(models) > 0,
                'available_models': [m['name'] for m in models]
            }
        else:
            return {'configured': False, 'error': 'Ollama not responding'}
    except Exception as e:
        return {'configured': False, 'error': str(e)}