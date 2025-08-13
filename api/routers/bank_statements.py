from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Dict, Any
from pathlib import Path
import os
import shutil
import uuid

from models.database import get_db
from sqlalchemy.orm import Session
from routers.auth import get_current_user
from models.models import MasterUser
from utils.rbac import require_non_viewer
from services.bank_statement_service import extract_transactions_from_pdf_paths


router = APIRouter(prefix="/bank-statements", tags=["bank-statements"])


@router.post("/upload", response_model=Dict[str, Any])
async def upload_bank_statements(
    files: List[UploadFile] = File(..., description="Up to 12 PDF bank statements"),
    db: Session = Depends(get_db),
    current_user: MasterUser = Depends(get_current_user),
):
    """Accept up to 12 PDF files, run extraction, and return transactions."""
    require_non_viewer(current_user, "upload bank statements")

    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")
    if len(files) > 12:
        raise HTTPException(status_code=400, detail="Maximum of 12 files are allowed")

    allowed_types = {"application/pdf"}
    saved_paths: List[str] = []

    try:
        # Save to tenant-scoped folder
        try:
            from models.database import get_tenant_context
            tenant_id = get_tenant_context()
        except Exception:
            tenant_id = None
        tenant_folder = f"tenant_{tenant_id}" if tenant_id else "tenant_unknown"
        base_dir = Path("attachments") / tenant_folder / "bank_statements"
        base_dir.mkdir(parents=True, exist_ok=True)

        for f in files:
            if f.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail="Only PDF files are supported")
            contents = await f.read()
            if len(contents) > 20 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Each file must be <= 20 MB")
            await f.seek(0)

            name = (f.filename or "statement.pdf").strip()
            name = os.path.basename(name)
            name = "".join(ch for ch in name if ch.isalnum() or ch in (".", "_", "-"))
            stem, _ext = os.path.splitext(name)
            unique = uuid.uuid4().hex
            out_path = base_dir / f"bs_{stem[:100]}_{unique}.pdf"
            with open(out_path, "wb") as out:
                shutil.copyfileobj(f.file, out)
            saved_paths.append(str(out_path))

        # Extract transactions
        transactions = extract_transactions_from_pdf_paths(saved_paths)

        # Map transaction_type to expense/income semantics is already debit/credit
        # Return raw; UI will allow editing/adding rows
        return {"success": True, "count": len(transactions), "transactions": transactions}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process bank statements: {e}")
    finally:
        # No cleanup: keep uploads under attachments for audit/debug
        pass


