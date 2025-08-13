import os
import re
import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


@dataclass
class Transaction:
    date: str
    description: str
    amount: float
    transaction_type: str  # 'debit' | 'credit'
    balance: Optional[float] = None
    category: Optional[str] = None


class SimplePDFLoader:
    """Best-effort PDF text loader with graceful fallbacks."""

    def __init__(self) -> None:
        self._loaders: List[Any] = []
        # Try to hydrate optional loaders in a preferred order
        try:
            from langchain_community.document_loaders import PDFPlumberLoader as LC_PDFPlumberLoader  # type: ignore
            self._loaders.append(("pdfplumber", LC_PDFPlumberLoader))
        except Exception:
            pass
        try:
            from langchain_community.document_loaders import PyMuPDFLoader as LC_PyMuPDFLoader  # type: ignore
            self._loaders.append(("pymupdf", LC_PyMuPDFLoader))
        except Exception:
            pass
        try:
            from langchain_community.document_loaders import PyPDFLoader as LC_PyPDFLoader  # type: ignore
            self._loaders.append(("pypdf", LC_PyPDFLoader))
        except Exception:
            pass

    def load(self, pdf_path: str) -> List[str]:
        path = str(pdf_path)
        last_err: Optional[Exception] = None
        for name, loader_cls in self._loaders:
            try:
                loader = loader_cls(path)
                docs = loader.load()
                if docs:
                    return [d.page_content or "" for d in docs]
            except Exception as e:  # pragma: no cover - best effort
                last_err = e
                continue

        # Final fallback using PyPDF2 only for raw text
        try:
            import PyPDF2  # type: ignore

            texts: List[str] = []
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    texts.append(page.extract_text() or "")
            return texts
        except Exception as e:  # pragma: no cover
            if last_err:
                raise last_err
            raise e


def _normalize_date(value: str) -> str:
    value = value.strip()
    fmts = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%Y/%m/%d"]
    for fmt in fmts:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    # Attempt to parse dd Mon yyyy like 01 Jan 2024
    try:
        return datetime.strptime(value, "%d %b %Y").strftime("%Y-%m-%d")
    except Exception:
        return value


def _regex_extract_transactions(text: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    # Common bank statement patterns: date description amount [balance]
    patterns = [
        r"(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<desc>[^\d\n]+?)\s+(?P<amount>-?\$?\d[\d,]*\.?\d*)\s*(?P<bal>\$?\d[\d,]*\.?\d*)?",
        r"(?P<date>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(?P<desc>[^\d\n]+?)\s+(?P<amount>-?\$?\d[\d,]*\.?\d*)\s*(?P<bal>\$?\d[\d,]*\.?\d*)?",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.MULTILINE):
            try:
                date = _normalize_date(m.group("date"))
                desc = re.sub(r"\s+", " ", m.group("desc").strip())
                amount_raw = (m.group("amount") or "0").replace("$", "").replace(",", "")
                amount = float(amount_raw)
                bal_group = m.group("bal")
                balance = None
                if bal_group:
                    try:
                        balance = float(bal_group.replace("$", "").replace(",", ""))
                    except Exception:
                        balance = None
                tx_type = "debit" if amount < 0 else "credit"
                results.append(
                    {
                        "date": date,
                        "description": desc,
                        "amount": amount,
                        "transaction_type": tx_type,
                        "balance": balance,
                    }
                )
            except Exception:
                continue
    return results


class BankStatementExtractor:
    """Extractor that uses Ollama when available, with regex fallback."""

    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "gpt-oss:latest")
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._ollama_available = self._check_ollama()
        self._pdf_loader = SimplePDFLoader()

    def _check_ollama(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code != 200:
                return False
            models = [m.get("name") for m in (resp.json().get("models") or [])]
            return self.model_name in models
        except Exception:
            return False

    def _ollama_chat(self, prompt: str) -> Optional[str]:
        try:
            # Use lightweight REST call to Ollama chat API
            payload = {"model": self.model_name, "messages": [{"role": "user", "content": prompt}], "stream": False, "temperature": 0.1}
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
            if resp.status_code == 200:
                data = resp.json()
                # Newer API returns message content in choices/message; fallback to old keys if needed
                if isinstance(data, dict) and "message" in data:
                    return data["message"].get("content", "")
                if "choices" in data and data["choices"]:
                    return data["choices"][0]["message"]["content"]
                return json.dumps(data)
            return None
        except Exception:
            return None

    def _build_extraction_prompt(self, text: str) -> str:
        return (
            "You are a financial data extraction expert. Extract bank transactions from the text below.\n\n"
            "RULES:\n"
            "1. Look for dates, descriptions, and amounts\n"
            "2. Amounts with '-' or in parentheses are debits (money out)\n"
            "3. Positive amounts are credits (money in)\n"
            "4. Convert dates to YYYY-MM-DD format\n"
            "5. Only extract actual transactions, not headers or summaries\n\n"
            "Return ONLY a JSON array like: \n"
            "[{\"date\": \"2024-01-15\", \"description\": \"GROCERY STORE\", \"amount\": -45.67, \"transaction_type\": \"debit\", \"balance\": 1234.56}]\n\n"
            f"TEXT:\n{text}\n\nJSON:"
        )

    def _parse_llm_json(self, content: str) -> List[Dict[str, Any]]:
        # Strip code fences if present
        s = re.sub(r"```json\s*|```", "", (content or "").strip())
        # Find first JSON array/object
        for pat in [r"\[[\s\S]*?\]", r"\{[\s\S]*?\}"]:
            m = re.search(pat, s)
            if not m:
                continue
            try:
                data = json.loads(m.group(0))
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return [data]
            except Exception:
                continue
        return []

    def extract_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        pages = self._pdf_loader.load(pdf_path)
        combined = "\n\n".join([re.sub(r"\s+", " ", p or "") for p in pages])

        if self._ollama_available:
            prompt = self._build_extraction_prompt(combined[:15000])  # cap tokens
            resp = self._ollama_chat(prompt)
            if resp:
                items = self._parse_llm_json(resp)
                if items:
                    return items

        # Fallback
        return _regex_extract_transactions(combined)

    def extract_from_files(self, files: List[str]) -> List[Dict[str, Any]]:
        all_items: List[Dict[str, Any]] = []
        for f in files:
            try:
                items = self.extract_from_pdf(f)
                all_items.extend(items)
            except Exception:
                continue

        # Normalize, infer transaction_type when missing, coerce fields
        normalized: List[Dict[str, Any]] = []
        for it in all_items:
            date = _normalize_date(str(it.get("date", "")).strip())
            desc = str(it.get("description", "")).strip() or "Unknown"
            try:
                amount = float(it.get("amount", 0))
            except Exception:
                # Try to clean currency formatting
                try:
                    amount = float(str(it.get("amount", 0)).replace("$", "").replace(",", ""))
                except Exception:
                    amount = 0.0
            tx_type = str(it.get("transaction_type", "")).lower() or ("debit" if amount < 0 else "credit")
            bal_val = it.get("balance", None)
            try:
                balance = float(bal_val) if bal_val is not None else None
            except Exception:
                balance = None

            normalized.append(
                {
                    "date": date,
                    "description": desc,
                    "amount": amount,
                    "transaction_type": "debit" if tx_type not in ("debit", "credit") else tx_type,
                    "balance": balance,
                    "category": it.get("category"),
                }
            )

        # De-duplicate basic duplicates
        seen = set()
        unique: List[Dict[str, Any]] = []
        for it in normalized:
            key = (it["date"], it["description"], round(float(it["amount"]), 2))
            if key in seen:
                continue
            seen.add(key)
            unique.append(it)

        # Sort by date
        try:
            unique.sort(key=lambda x: x["date"])  # YYYY-MM-DD lexicographic works
        except Exception:
            pass

        return unique


def extract_transactions_from_pdf_paths(pdf_paths: List[str]) -> List[Dict[str, Any]]:
    extractor = BankStatementExtractor()
    return extractor.extract_from_files(pdf_paths)


