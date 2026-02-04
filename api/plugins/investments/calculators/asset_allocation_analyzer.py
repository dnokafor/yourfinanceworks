"""
Asset Allocation Analyzer

This module implements asset allocation analysis for investment portfolios.
It provides methods to calculate asset allocation by asset class, ensuring
percentages sum to 100% and handling empty portfolios appropriately.

The analyzer follows the design specification for asset allocation metrics
and integrates with the existing holding data structures.
"""

from typing import List, Dict
from decimal import Decimal

from ..models import InvestmentHolding, AssetClass
from ..schemas import AssetAllocation, AllocationDetail


class AssetAllocationAnalyzer:
    """
    Analyzer for investment asset allocation.

    This class provides methods to calculate asset allocation across different
    asset classes, ensuring proper percentage calculations and handling edge cases.
    """

    def calculate_asset_allocation(self, holdings: List[InvestmentHolding]) -> AssetAllocation:
        """
        Calculate asset allocation by asset class.

        Groups holdings by asset class and calculates the value and percentage
        for each class. Ensures percentages sum to 100% and handles empty portfolios.

        Args:
            holdings: List of portfolio holdings

        Returns:
            AssetAllocation object with allocation details by asset class
        """
        # Initialize allocation tracking
        allocation_map: Dict[AssetClass, Dict[str, any]] = {}
        total_value = Decimal('0')

        # Process each holding
        for holding in holdings:
            # Skip closed holdings
            if holding.is_closed or holding.quantity <= 0:
                continue

            # Calculate holding value
            holding_value = self._calculate_holding_value(holding)
            total_value += holding_value

            # Group by asset class
            asset_class = holding.asset_class
            if asset_class not in allocation_map:
                allocation_map[asset_class] = {
                    "value": Decimal('0'),
                    "holdings_count": 0
                }

            allocation_map[asset_class]["value"] += holding_value
            allocation_map[asset_class]["holdings_count"] += 1

        # Calculate percentages and create allocation details
        allocations: Dict[AssetClass, AllocationDetail] = {}

        if total_value > 0:
            # Calculate percentages ensuring they sum to 100%
            calculated_percentages = {}
            total_percentage = Decimal('0')

            # Calculate raw percentages
            for asset_class, data in allocation_map.items():
                percentage = (data["value"] / total_value) * Decimal('100')
                calculated_percentages[asset_class] = percentage
                total_percentage += percentage

            # Adjust for rounding errors to ensure sum equals 100%
            if total_percentage != Decimal('100') and len(calculated_percentages) > 0:
                # Find the asset class with the largest value to adjust
                largest_asset_class = max(allocation_map.keys(), key=lambda ac: allocation_map[ac]["value"])
                adjustment = Decimal('100') - total_percentage
                calculated_percentages[largest_asset_class] += adjustment

            # Create allocation details
            for asset_class, data in allocation_map.items():
                allocations[asset_class] = AllocationDetail(
                    asset_class=asset_class,
                    value=data["value"],
                    percentage=calculated_percentages[asset_class],
                    holdings_count=data["holdings_count"]
                )
        else:
            # Empty portfolio - no allocations
            pass

        return AssetAllocation(
            allocations=allocations,
            total_value=total_value
        )

    def _calculate_holding_value(self, holding: InvestmentHolding) -> Decimal:
        """
        Calculate the current value of a holding.

        Uses current price if available, otherwise falls back to cost basis per share.

        Args:
            holding: Investment holding

        Returns:
            Current value of the holding
        """
        if holding.current_price and holding.current_price > 0:
            # Use current market price
            return Decimal(str(holding.quantity)) * Decimal(str(holding.current_price))
        else:
            # Fallback to cost basis (original purchase value)
            return Decimal(str(holding.cost_basis))

    def get_asset_class_summary(self, holdings: List[InvestmentHolding]) -> Dict[AssetClass, Dict[str, any]]:
        """
        Get a summary of holdings by asset class.

        Args:
            holdings: List of portfolio holdings

        Returns:
            Dictionary mapping asset classes to summary information
        """
        summary = {}

        for holding in holdings:
            # Skip closed holdings
            if holding.is_closed or holding.quantity <= 0:
                continue

            asset_class = holding.asset_class
            if asset_class not in summary:
                summary[asset_class] = {
                    "holdings": [],
                    "total_value": Decimal('0'),
                    "total_cost_basis": Decimal('0'),
                    "holdings_count": 0
                }

            holding_value = self._calculate_holding_value(holding)
            cost_basis = Decimal(str(holding.cost_basis))

            summary[asset_class]["holdings"].append(holding)
            summary[asset_class]["total_value"] += holding_value
            summary[asset_class]["total_cost_basis"] += cost_basis
            summary[asset_class]["holdings_count"] += 1

        return summary

    def calculate_diversification_score(self, holdings: List[InvestmentHolding]) -> Decimal:
        """
        Calculate a simple diversification score based on asset class distribution.

        The score is based on how evenly distributed the portfolio is across asset classes.
        A perfectly diversified portfolio across all asset classes would score 100.

        Args:
            holdings: List of portfolio holdings

        Returns:
            Diversification score (0-100)
        """
        allocation = self.calculate_asset_allocation(holdings)

        if not allocation.allocations or allocation.total_value == 0:
            return Decimal('0')

        # Calculate how evenly distributed the allocations are
        num_asset_classes = len(allocation.allocations)
        if num_asset_classes == 0:
            return Decimal('0')

        # Ideal percentage per asset class for perfect distribution
        ideal_percentage = Decimal('100') / Decimal(str(num_asset_classes))

        # Calculate variance from ideal distribution
        total_variance = Decimal('0')
        for allocation_detail in allocation.allocations.values():
            variance = abs(allocation_detail.percentage - ideal_percentage)
            total_variance += variance

        # Convert variance to a score (lower variance = higher score)
        max_possible_variance = Decimal('100') * (Decimal(str(num_asset_classes)) - 1) / Decimal(str(num_asset_classes))
        if max_possible_variance > 0:
            score = (1 - (total_variance / (2 * max_possible_variance))) * Decimal('100')
            return max(Decimal('0'), score)

        return Decimal('100')  # Single asset class is perfectly "diversified" within that class

    def get_largest_holdings_by_asset_class(
        self,
        holdings: List[InvestmentHolding],
        asset_class: AssetClass,
        limit: int = 5
    ) -> List[InvestmentHolding]:
        """
        Get the largest holdings within a specific asset class.

        Args:
            holdings: List of portfolio holdings
            asset_class: Asset class to filter by
            limit: Maximum number of holdings to return

        Returns:
            List of holdings sorted by value (descending)
        """
        # Filter holdings by asset class
        filtered_holdings = [
            holding for holding in holdings
            if holding.asset_class == asset_class and not holding.is_closed and holding.quantity > 0
        ]

        # Sort by value (descending)
        sorted_holdings = sorted(
            filtered_holdings,
            key=lambda h: self._calculate_holding_value(h),
            reverse=True
        )

        return sorted_holdings[:limit]