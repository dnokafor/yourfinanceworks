"""
Portfolio Data Exporter

This module implements full portfolio data export functionality for investment portfolios.
It provides methods to export complete portfolio data including holdings, transactions,
and performance metrics in CSV and JSON formats for backup and data portability purposes.

This is separate from the tax-specific export and provides comprehensive portfolio data
for backup, migration, or analysis purposes.
"""

import csv
import json
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date, datetime
from io import StringIO

from ..models import InvestmentPortfolio, InvestmentHolding, InvestmentTransaction
from ..schemas import PortfolioResponse, HoldingResponse, TransactionResponse


class PortfolioDataExporter:
    """
    Exporter for complete portfolio data.

    This class provides methods to export comprehensive portfolio data including
    holdings, transactions, and performance metrics for backup and data portability.
    """

    def export_portfolio_data(
        self,
        portfolio: InvestmentPortfolio,
        holdings: List[InvestmentHolding],
        transactions: List[InvestmentTransaction],
        performance_data: Optional[Dict[str, Any]] = None,
        format: str = "json"
    ) -> str:
        """
        Export complete portfolio data in CSV or JSON format.

        Args:
            portfolio: Portfolio to export
            holdings: List of holdings in the portfolio
            transactions: List of transactions in the portfolio
            performance_data: Optional performance metrics
            format: Export format ("csv" or "json")

        Returns:
            Exported data as string

        Raises:
            ValueError: If format is not supported
        """
        if format.lower() == "csv":
            return self._export_csv(portfolio, holdings, transactions, performance_data)
        elif format.lower() == "json":
            return self._export_json(portfolio, holdings, transactions, performance_data)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def export_transactions_csv(
        self,
        transactions: List[InvestmentTransaction],
        portfolio_name: str = ""
    ) -> str:
        """
        Export transactions to CSV format for spreadsheet analysis.

        Args:
            transactions: List of transactions to export
            portfolio_name: Name of the portfolio (for reference)

        Returns:
            CSV data as string
        """
        output = StringIO()

        # Define CSV headers for transaction export
        headers = [
            'Transaction ID',
            'Portfolio Name',
            'Transaction Date',
            'Transaction Type',
            'Security Symbol',
            'Security Name',
            'Quantity',
            'Price Per Share',
            'Total Amount',
            'Fees',
            'Realized Gain/Loss',
            'Dividend Type',
            'Payment Date',
            'Ex-Dividend Date',
            'Notes',
            'Created At'
        ]

        writer = csv.writer(output)
        writer.writerow(headers)

        # Sort transactions by date
        sorted_transactions = sorted(transactions, key=lambda x: x.transaction_date)

        # Write transaction data
        for transaction in sorted_transactions:
            # Get security information from holding if available
            security_symbol = ""
            security_name = ""
            if transaction.holding:
                security_symbol = transaction.holding.security_symbol
                security_name = transaction.holding.security_name or ""

            row = [
                transaction.id,
                portfolio_name,
                transaction.transaction_date.isoformat(),
                transaction.transaction_type.value.upper(),
                security_symbol,
                security_name,
                str(transaction.quantity) if transaction.quantity else "",
                str(transaction.price_per_share) if transaction.price_per_share else "",
                str(transaction.total_amount),
                str(transaction.fees) if transaction.fees else "0.00",
                str(transaction.realized_gain) if transaction.realized_gain else "",
                transaction.dividend_type.value.upper() if transaction.dividend_type else "",
                transaction.payment_date.isoformat() if transaction.payment_date else "",
                transaction.ex_dividend_date.isoformat() if transaction.ex_dividend_date else "",
                transaction.notes or "",
                transaction.created_at.isoformat()
            ]
            writer.writerow(row)

        return output.getvalue()

    def export_holdings_csv(
        self,
        holdings: List[InvestmentHolding],
        portfolio_name: str = ""
    ) -> str:
        """
        Export holdings to CSV format for spreadsheet analysis.

        Args:
            holdings: List of holdings to export
            portfolio_name: Name of the portfolio (for reference)

        Returns:
            CSV data as string
        """
        output = StringIO()

        # Define CSV headers for holdings export
        headers = [
            'Holding ID',
            'Portfolio Name',
            'Security Symbol',
            'Security Name',
            'Security Type',
            'Asset Class',
            'Quantity',
            'Cost Basis',
            'Average Cost Per Share',
            'Current Price',
            'Current Value',
            'Unrealized Gain/Loss',
            'Purchase Date',
            'Price Updated At',
            'Is Closed',
            'Created At',
            'Updated At'
        ]

        writer = csv.writer(output)
        writer.writerow(headers)

        # Sort holdings by security symbol
        sorted_holdings = sorted(holdings, key=lambda x: x.security_symbol)

        # Write holdings data
        for holding in sorted_holdings:
            row = [
                holding.id,
                portfolio_name,
                holding.security_symbol,
                holding.security_name or "",
                holding.security_type.value.upper(),
                holding.asset_class.value.upper(),
                str(holding.quantity),
                str(holding.cost_basis),
                str(holding.average_cost_per_share),
                str(holding.current_price) if holding.current_price else "",
                str(holding.current_value),
                str(holding.unrealized_gain_loss),
                holding.purchase_date.isoformat(),
                holding.price_updated_at.isoformat() if holding.price_updated_at else "",
                "Yes" if holding.is_closed else "No",
                holding.created_at.isoformat(),
                holding.updated_at.isoformat()
            ]
            writer.writerow(row)

        return output.getvalue()

    def _export_csv(
        self,
        portfolio: InvestmentPortfolio,
        holdings: List[InvestmentHolding],
        transactions: List[InvestmentTransaction],
        performance_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export complete portfolio data to CSV format (multiple sections).

        Args:
            portfolio: Portfolio to export
            holdings: List of holdings
            transactions: List of transactions
            performance_data: Optional performance metrics

        Returns:
            CSV data as string with multiple sections
        """
        output = StringIO()
        writer = csv.writer(output)

        # Portfolio summary section
        writer.writerow(['PORTFOLIO SUMMARY'])
        writer.writerow(['Portfolio ID', portfolio.id])
        writer.writerow(['Portfolio Name', portfolio.name])
        writer.writerow(['Portfolio Type', portfolio.portfolio_type.value.upper()])
        writer.writerow(['Created At', portfolio.created_at.isoformat()])
        writer.writerow(['Updated At', portfolio.updated_at.isoformat()])
        writer.writerow(['Is Archived', 'Yes' if portfolio.is_archived else 'No'])

        # Performance data section (if provided)
        if performance_data:
            writer.writerow([])
            writer.writerow(['PERFORMANCE METRICS'])
            for key, value in performance_data.items():
                writer.writerow([key.replace('_', ' ').title(), str(value)])

        # Holdings section
        writer.writerow([])
        writer.writerow(['HOLDINGS'])
        holdings_csv = self.export_holdings_csv(holdings, portfolio.name)
        # Skip the header row from holdings CSV and add the data
        holdings_lines = holdings_csv.strip().split('\n')
        for line in holdings_lines:
            writer.writerow(line.split(','))

        # Transactions section
        writer.writerow([])
        writer.writerow(['TRANSACTIONS'])
        transactions_csv = self.export_transactions_csv(transactions, portfolio.name)
        # Skip the header row from transactions CSV and add the data
        transactions_lines = transactions_csv.strip().split('\n')
        for line in transactions_lines:
            writer.writerow(line.split(','))

        return output.getvalue()

    def _export_json(
        self,
        portfolio: InvestmentPortfolio,
        holdings: List[InvestmentHolding],
        transactions: List[InvestmentTransaction],
        performance_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export complete portfolio data to JSON format.

        Args:
            portfolio: Portfolio to export
            holdings: List of holdings
            transactions: List of transactions
            performance_data: Optional performance metrics

        Returns:
            JSON data as string
        """
        # Build the complete export data structure
        export_data = {
            "export_metadata": {
                "export_date": datetime.now().isoformat(),
                "export_type": "complete_portfolio_data",
                "version": "1.0"
            },
            "portfolio": {
                "id": portfolio.id,
                "name": portfolio.name,
                "portfolio_type": portfolio.portfolio_type.value,
                "is_archived": portfolio.is_archived,
                "created_at": portfolio.created_at.isoformat(),
                "updated_at": portfolio.updated_at.isoformat()
            },
            "performance": performance_data or {},
            "holdings": [],
            "transactions": [],
            "summary": {
                "total_holdings": len(holdings),
                "active_holdings": len([h for h in holdings if not h.is_closed]),
                "closed_holdings": len([h for h in holdings if h.is_closed]),
                "total_transactions": len(transactions),
                "transaction_types": self._get_transaction_type_counts(transactions)
            }
        }

        # Add holdings data
        for holding in holdings:
            holding_data = {
                "id": holding.id,
                "security_symbol": holding.security_symbol,
                "security_name": holding.security_name,
                "security_type": holding.security_type.value,
                "asset_class": holding.asset_class.value,
                "quantity": str(holding.quantity),
                "cost_basis": str(holding.cost_basis),
                "average_cost_per_share": str(holding.average_cost_per_share),
                "current_price": str(holding.current_price) if holding.current_price else None,
                "current_value": str(holding.current_value),
                "unrealized_gain_loss": str(holding.unrealized_gain_loss),
                "purchase_date": holding.purchase_date.isoformat(),
                "price_updated_at": holding.price_updated_at.isoformat() if holding.price_updated_at else None,
                "is_closed": holding.is_closed,
                "created_at": holding.created_at.isoformat(),
                "updated_at": holding.updated_at.isoformat()
            }
            export_data["holdings"].append(holding_data)

        # Add transactions data (sorted by date)
        sorted_transactions = sorted(transactions, key=lambda x: x.transaction_date)
        for transaction in sorted_transactions:
            transaction_data = {
                "id": transaction.id,
                "holding_id": transaction.holding_id,
                "transaction_type": transaction.transaction_type.value,
                "transaction_date": transaction.transaction_date.isoformat(),
                "security_symbol": transaction.holding.security_symbol if transaction.holding else None,
                "quantity": str(transaction.quantity) if transaction.quantity else None,
                "price_per_share": str(transaction.price_per_share) if transaction.price_per_share else None,
                "total_amount": str(transaction.total_amount),
                "fees": str(transaction.fees) if transaction.fees else "0.00",
                "realized_gain": str(transaction.realized_gain) if transaction.realized_gain else None,
                "dividend_type": transaction.dividend_type.value if transaction.dividend_type else None,
                "payment_date": transaction.payment_date.isoformat() if transaction.payment_date else None,
                "ex_dividend_date": transaction.ex_dividend_date.isoformat() if transaction.ex_dividend_date else None,
                "notes": transaction.notes,
                "created_at": transaction.created_at.isoformat()
            }
            export_data["transactions"].append(transaction_data)

        return json.dumps(export_data, indent=2, default=str)

    def _get_transaction_type_counts(self, transactions: List[InvestmentTransaction]) -> Dict[str, int]:
        """
        Get counts of each transaction type.

        Args:
            transactions: List of transactions

        Returns:
            Dictionary with transaction type counts
        """
        counts = {}
        for transaction in transactions:
            tx_type = transaction.transaction_type.value
            counts[tx_type] = counts.get(tx_type, 0) + 1
        return counts

    def get_portfolio_backup_data(
        self,
        portfolio: InvestmentPortfolio,
        holdings: List[InvestmentHolding],
        transactions: List[InvestmentTransaction],
        performance_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get complete portfolio data for backup purposes.

        This method returns a comprehensive data structure that can be used
        for backup, migration, or analysis purposes.

        Args:
            portfolio: Portfolio to backup
            holdings: List of holdings
            transactions: List of transactions
            performance_data: Optional performance metrics

        Returns:
            Dictionary with complete portfolio data
        """
        # Calculate summary statistics
        total_cost_basis = sum(Decimal(str(h.cost_basis)) for h in holdings if not h.is_closed)
        total_current_value = sum(h.current_value for h in holdings if not h.is_closed)
        total_unrealized_gain = total_current_value - total_cost_basis

        # Calculate realized gains from transactions
        total_realized_gains = sum(
            Decimal(str(tx.realized_gain)) for tx in transactions
            if tx.realized_gain is not None
        )

        # Calculate dividend income
        total_dividends = sum(
            Decimal(str(tx.total_amount)) for tx in transactions
            if tx.transaction_type.value == 'dividend'
        )

        backup_data = {
            "backup_metadata": {
                "backup_date": datetime.now().isoformat(),
                "portfolio_id": portfolio.id,
                "portfolio_name": portfolio.name,
                "data_version": "1.0"
            },
            "portfolio_info": {
                "id": portfolio.id,
                "name": portfolio.name,
                "portfolio_type": portfolio.portfolio_type.value,
                "is_archived": portfolio.is_archived,
                "created_at": portfolio.created_at.isoformat(),
                "updated_at": portfolio.updated_at.isoformat()
            },
            "summary_statistics": {
                "total_holdings": len(holdings),
                "active_holdings": len([h for h in holdings if not h.is_closed]),
                "closed_holdings": len([h for h in holdings if h.is_closed]),
                "total_transactions": len(transactions),
                "total_cost_basis": str(total_cost_basis),
                "total_current_value": str(total_current_value),
                "total_unrealized_gain": str(total_unrealized_gain),
                "total_realized_gains": str(total_realized_gains),
                "total_dividend_income": str(total_dividends)
            },
            "performance_data": performance_data or {},
            "holdings_data": [
                {
                    "id": h.id,
                    "security_symbol": h.security_symbol,
                    "security_name": h.security_name,
                    "security_type": h.security_type.value,
                    "asset_class": h.asset_class.value,
                    "quantity": str(h.quantity),
                    "cost_basis": str(h.cost_basis),
                    "current_price": str(h.current_price) if h.current_price else None,
                    "purchase_date": h.purchase_date.isoformat(),
                    "is_closed": h.is_closed,
                    "created_at": h.created_at.isoformat(),
                    "updated_at": h.updated_at.isoformat()
                }
                for h in holdings
            ],
            "transactions_data": [
                {
                    "id": tx.id,
                    "holding_id": tx.holding_id,
                    "transaction_type": tx.transaction_type.value,
                    "transaction_date": tx.transaction_date.isoformat(),
                    "quantity": str(tx.quantity) if tx.quantity else None,
                    "price_per_share": str(tx.price_per_share) if tx.price_per_share else None,
                    "total_amount": str(tx.total_amount),
                    "fees": str(tx.fees) if tx.fees else "0.00",
                    "realized_gain": str(tx.realized_gain) if tx.realized_gain else None,
                    "notes": tx.notes,
                    "created_at": tx.created_at.isoformat()
                }
                for tx in sorted(transactions, key=lambda x: x.transaction_date)
            ]
        }

        return backup_data