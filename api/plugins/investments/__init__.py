"""
Investment Management Plugin for YourFinanceWORKS

This plugin provides comprehensive investment portfolio tracking, performance analytics,
and tax reporting capabilities. It's designed as a self-contained commercial feature
that integrates with the existing multi-tenant architecture.

Features:
- Portfolio management (TAXABLE, RETIREMENT, BUSINESS)
- Holdings tracking with cost basis
- Transaction recording (BUY, SELL, DIVIDEND, etc.)
- Performance analytics (inception-to-date)
- Asset allocation analysis
- Dividend tracking
- Tax data export
- MCP assistant integration

License: Commercial tier required
"""

from fastapi import APIRouter, Depends
from core.utils.feature_gate import require_feature

def register_investment_plugin(app, mcp_registry=None, feature_gate=None):
    """
    Register the investment management plugin with the main application.
    This is a COMMERCIAL feature requiring a commercial license.

    Args:
        app: FastAPI application instance
        mcp_registry: MCP provider registry (optional)
        feature_gate: Feature gate service (optional)

    Returns:
        dict: Plugin metadata
    """
    from .router import investment_router

    # Register API routes under /api/v1/investments
    # All routes protected by commercial license requirement
    if feature_gate:
        app.include_router(
            investment_router,
            prefix="/api/v1/investments",
            tags=["investments"],
            dependencies=[Depends(lambda: require_feature("investments", tier="commercial"))]
        )
    else:
        # For development/testing without feature gate
        app.include_router(
            investment_router,
            prefix="/api/v1/investments",
            tags=["investments"]
        )

    # Register MCP provider for AI assistant (if available)
    if mcp_registry:
        try:
            from .mcp.investment_provider import InvestmentMCPProvider
            mcp_registry.register_provider("investments", InvestmentMCPProvider())
        except ImportError:
            # MCP provider is optional
            pass

    return {
        "name": "investment-management",
        "version": "1.0.0",
        "license_tier": "commercial",
        "routes": ["/api/v1/investments"],
        "mcp_providers": ["investments"] if mcp_registry else [],
        "description": "Investment portfolio tracking and analytics"
    }