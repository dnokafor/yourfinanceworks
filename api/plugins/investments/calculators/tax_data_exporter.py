"""
Tax Data Exporter

This module implements tax-related data export functionality for investment portfolios.
It provides methods to export transaction data in CSV and JSON formats, calculate
realized gains and dividend income as raw amounts without tax classification.

This is specifically for tax-related data export to provide raw transaction data
to accountants or tax software for proper tax preparation.
"""

import csv
import json
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date
from io import StringIO

from ..models import InvestmentTransaction, TransactionType
from ..schemas import TaxExport, TransactionResponse


class TaxDataExporter:
    """
    Exporter for tax-related investment data.

    This class provides methods to export transaction data and calculate
    tax-relevant metrics like realized gains and dividend income as raw amounts
    without tax classification or jurisdiction-specific rules.
    """

    def export_transaction_data(
        self,
        transactions: List[InvestmentTransaction],
        tax_year: int,
        format: str = "csv"
    ) -> str:
        """
        Export transaction data in CSV or JSON format for tax purposes.

        Includes all transaction details needed by accountants or tax software.

        Args:
            transactions: List of transactions to export
            tax_year: Tax year for the export
            format: Export format ("csv" or "json")

        Returns:
            Exported data as string

        Raises:
            ValueError: If format is not supported
        """
        if format.lower() == "csv":
            return self._export_csv(transactions, tax_year)
        elif format.lower() == "json":
            return self._export_json(transactions, tax_year)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def calculate_realized_gains(
        self,
        transactions: List[InvestmentTransaction],
        tax_year: Optional[int] = None
    ) -> Decimal:
        """
        Calculate total realized gains as raw amounts (no classification).

        Sums up all realized gains from SELL transactions for the specified year.
        Returns raw amounts without any tax classification or jurisdiction-specific rules.

        Args:
            transactions: List of transactions
            tax_year: Tax year to filter by (optional)

        Returns:
            Total realized gains (can be negative for losses)
        """
        total_realized_gains = Decimal('0')

        for transaction in transactions:
            if transaction.transaction_type == TransactionType.SELL:
                # Filter by tax year if specified
                if tax_year and transaction.transaction_date.year != tax_year:
                    continue

                if transaction.realized_gain is not None:
                    total_realized_gains += Decimal(str(transaction.realized_gain))

        return total_realized_gains

    def calculate_dividend_income(
        self,
        transactions: List[InvestmentTransaction],
        tax_year: Optional[int] = None
    ) -> Decimal:
        """
        Calculate total dividend income as raw amounts (no classification).

        Sums up all dividend payments for the specified year.
        Returns raw amounts without any tax classification or jurisdiction-specific rules.

        Args:
            transactions: List of transactions
            tax_year: Tax year to filter by (optional)

        Returns:
            Total dividend income
        """
        total_dividends = Decimal('0')

        for transaction in transactions:
            if transaction.transaction_type == TransactionType.DIVIDEND:
                # Filter by tax year if specified
                if tax_year and transaction.transaction_date.year != tax_year:
                    continue

                total_dividends += Decimal(str(transaction.total_amount))

        return total_dividends

    def get_tax_export_data(
        self,
        transactions: List[InvestmentTransaction],
        tax_year: int
    ) -> TaxExport:
        """
        Get comprehensive tax export data for a specific year.

        Args:
            transactions: List of all transactions
            tax_year: Tax year to export

        Returns:
            TaxExport object with all tax-relevant data
        """
        # Filter transactions by tax year
        year_transactions = [
            tx for tx in transactions
            if tx.transaction_date.year == tax_year
        ]

        # Calculate totals
        total_realized_gains = self.calculate_realized_gains(year_transactions)
        total_dividends = self.calculate_dividend_income(year_transactions)

        # Convert to response format
        transaction_responses = [
            TransactionResponse.model_validate(tx) for tx in year_transactions
        ]

        return TaxExport(
            tax_year=tax_year,
            total_realized_gains=total_realized_gains,
            total_dividends=total_dividends,
            transactions=transaction_responses
        )

    def _export_csv(self, transactions: List[InvestmentTransaction], tax_year: int) -> str:
        """
        Export transactions to CSV format.

        Args:
            transactions: List of transactions to export
            tax_year: Tax year for the export

        Returns:
            CSV data as string
        """
        output = StringIO()

        # Define CSV headers
        headers = [
            'Transaction ID',
            'Portfolio ID',
            'Holding ID',
            'Transaction Type',
            'Transaction Date',
            'Security Symbol',
            'Quantity',
            'Price Per Share',
            'Total Amount',
            'Fees',
            'Realized Gain',
            'Dividend Type',
            'Payment Date',
            'Ex-Dividend Date',
            'Notes',
            'Created At'
        ]

        writer = csv.writer(output)
        writer.writerow(headers)

        # Filter transactions by tax year
        year_transactions = [
            tx for tx in transactions
            if tx.transaction_date.year == tax_year
        ]

        # Write transaction data
        for transaction in year_transactions:
            # Get security symbol from holding if available
            security_symbol = ""
            if transaction.holding:
                security_symbol = transaction.holding.security_symbol

            row = [
                transaction.id,
                transaction.portfolio_id,
                transaction.holding_id or "",
                transaction.transaction_type.value,
                transaction.transaction_date.isoformat(),
                security_symbol,
                str(transaction.quantity) if transaction.quantity else "",
                str(transaction.price_per_share) if transaction.price_per_share else "",
                str(transaction.total_amount),
                str(transaction.fees) if transaction.fees else "0",
                str(transaction.realized_gain) if transaction.realized_gain else "",
                transaction.dividend_type.value if transaction.dividend_type else "",
                transaction.payment_date.isoformat() if transaction.payment_date else "",
                transaction.ex_dividend_date.isoformat() if transaction.ex_dividend_date else "",
                transaction.notes or "",
                transaction.created_at.isoformat()
            ]
            writer.writerow(row)

        return output.getvalue()

    def _export_json(self, transactions: List[InvestmentTransaction], tax_year: int) -> str:
        """
        Export transactions to JSON format.

        Args:
            transactions: List of transactions to export
            tax_year: Tax year for the export

        Returns:
            JSON data as string
        """
        # Filter transactions by tax year
        year_transactions = [
            tx for tx in transactions
            if tx.transaction_date.year == tax_year
        ]

        # Convert transactions to dictionaries
        export_data = {
            "tax_year": tax_year,
            "export_date": date.today().isoformat(),
            "total_transactions": len(year_transactions),
            "total_realized_gains": str(self.calculate_realized_gains(year_transactions)),
            "total_dividends": str(self.calculate_dividend_income(year_transactions)),
            "transactions": []
        }

        for transaction in year_transactions:
            # Get security symbol from holding if available
            security_symbol = ""
            if transaction.holding:
                security_symbol = transaction.holding.security_symbol

            transaction_data = {
                "transaction_id": transaction.id,
                "portfolio_id": transaction.portfolio_id,
                "holding_id": transaction.holding_id,
                "transaction_type": transaction.transaction_type.value,
                "transaction_date": transaction.transaction_date.isoformat(),
                "security_symbol": security_symbol,
                "quantity": str(transaction.quantity) if transaction.quantity else None,
                "price_per_share": str(transaction.price_per_share) if transaction.price_per_share else None,
                "total_amount": str(transaction.total_amount),
                "fees": str(transaction.fees) if transaction.fees else "0",
                "realized_gain": str(transaction.realized_gain) if transaction.realized_gain else None,
                "dividend_type": transaction.dividend_type.value if transaction.dividend_type else None,
                "payment_date": transaction.payment_date.isoformat() if transaction.payment_date else None,
                "ex_dividend_date": transaction.ex_dividend_date.isoformat() if transaction.ex_dividend_date else None,
                "notes": transaction.notes,
                "created_at": transaction.created_at.isoformat()
            }
            export_data["transactions"].append(transaction_data)

        return json.dumps(export_data, indent=2, default=str)

    def get_capital_gains_summary(
        self,
        transactions: List[InvestmentTransaction],
        tax_year: int
    ) -> Dict[str, Any]:
        """
        Get a summary of capital gains for tax reporting.

        Args:
            transactions: List of transactions
            tax_year: Tax year to summarize

        Returns:
            Dictionary with capital gains summary
        """
        # Filter sell transactions by tax year
        sell_transactions = [
            tx for tx in transactions
            if tx.transaction_type == TransactionType.SELL
            and tx.transaction_date.year == tax_year
        ]

        total_gains = Decimal('0')
        total_losses = Decimal('0')
        transaction_count = 0

        for transaction in sell_transactions:
            if transaction.realized_gain is not None:
                realized_gain = Decimal(str(transaction.realized_gain))
                if realized_gain >= 0:
                    total_gains += realized_gain
                else:
                    total_losses += abs(realized_gain)
                transaction_count += 1

        net_gain_loss = total_gains - total_losses

        return {
            "tax_year": tax_year,
            "total_gains": str(total_gains),
            "total_losses": str(total_losses),
            "net_gain_loss": str(net_gain_loss),
            "transaction_count": transaction_count,
            "transactions": [
                {
                    "transaction_id": tx.id,
                    "transaction_date": tx.transaction_date.isoformat(),
                    "security_symbol": tx.holding.security_symbol if tx.holding else "",
                    "quantity": str(tx.quantity) if tx.quantity else "",
                    "realized_gain": str(tx.realized_gain) if tx.realized_gain else "0"
                }
                for tx in sell_transactions
            ]
        }

    def get_dividend_summary(
        self,
        transactions: List[InvestmentTransaction],
        tax_year: int
    ) -> Dict[str, Any]:
        """
        Get a summary of dividend income for tax reporting.

        Args:
            transactions: List of transactions
            tax_year: Tax year to summarize

        Returns:
            Dictionary with dividend summary
        """
        # Filter dividend transactions by tax year
        dividend_transactions = [
            tx for tx in transactions
            if tx.transaction_type == TransactionType.DIVIDEND
            and tx.transaction_date.year == tax_year
        ]

        total_dividends = Decimal('0')
        dividend_count = 0

        for transaction in dividend_transactions:
            total_dividends += Decimal(str(transaction.total_amount))
            dividend_count += 1

        return {
            "tax_year": tax_year,
            "total_dividends": str(total_dividends),
            "dividend_count": dividend_count,
            "transactions": [
                {
                    "transaction_id": tx.id,
                    "transaction_date": tx.transaction_date.isoformat(),
                    "payment_date": tx.payment_date.isoformat() if tx.payment_date else None,
                    "security_symbol": tx.holding.security_symbol if tx.holding else "",
                    "dividend_amount": str(tx.total_amount),
                    "dividend_type": tx.dividend_type.value if tx.dividend_type else "ordinary"
                }
                for tx in dividend_transactions
            ]
        }