# Analytics Tab Implementation

## Overview
Implemented a comprehensive Analytics tab for the Portfolio Detail page that provides insights into diversification, dividend income, and payment patterns.

## What Was Added

### Frontend Components

#### 1. PortfolioAnalytics Component (`ui/src/components/investments/PortfolioAnalytics.tsx`)
A new React component that displays:

**Diversification Analysis**
- Diversification score (0-100)
- Classification: Well Diversified / Moderately Diversified / Concentrated
- Concentration risk warning if largest holding > 30%
- Actionable recommendations based on score

**Dividend Yields**
- Per-holding dividend yield percentages
- Based on last 12 months of dividend payments
- Scrollable list for portfolios with many holdings

**Dividend Payment Frequency**
- Historical payment patterns for each dividend-paying holding
- Frequency classification (Monthly, Quarterly, Semi-Annual, Annual, Irregular)
- Average payment amount and interval
- Last payment date

**Dividend Forecast**
- Projected dividend income for next 3, 6, 12, or 24 months
- Breakdown by holding
- Based on historical payment patterns

**Information Box**
- Explains each metric and how it's calculated

### Backend Endpoints

#### 1. New API Endpoint
- `GET /investments/portfolios/{portfolio_id}/diversification`
- Returns diversification analysis including:
  - Diversification score
  - Concentration risk metrics
  - Asset class distribution

### API Client Methods

Added to `investmentApi` in `ui/src/lib/api.ts`:
- `getDividendYields(portfolioId)` - Get dividend yields by holding
- `getDividendFrequency(portfolioId)` - Get payment frequency analysis
- `getDividendForecast(portfolioId, forecastMonths)` - Get projected dividend income
- `getDiversificationAnalysis(portfolioId)` - Get diversification metrics

### UI Integration

Updated `PortfolioDetail.tsx`:
- Replaced "Advanced analytics coming soon..." placeholder with PortfolioAnalytics component
- Removed unused imports (Plus, Settings)
- Added PortfolioAnalytics import

## Features

### Diversification Analysis
- **Score Calculation**: Measures spread across asset classes
- **Risk Assessment**: Identifies concentration risk
- **Recommendations**: Suggests diversification improvements
- **Visual Indicators**: Color-coded (green/amber/red) based on score

### Dividend Intelligence
- **Yield Tracking**: Shows dividend income as % of holding value
- **Pattern Recognition**: Identifies payment frequency patterns
- **Income Forecasting**: Projects future dividend income
- **Historical Data**: Based on actual transaction history

### User Experience
- Loading states with spinner
- Responsive grid layouts (mobile, tablet, desktop)
- Scrollable lists for large datasets
- Color-coded risk indicators
- Helpful info box explaining metrics
- Forecast period selector (3/6/12/24 months)

## Data Sources

All analytics are calculated from existing data:
- Holdings data (quantity, current price, cost basis)
- Transaction history (dividend transactions)
- Portfolio structure (asset classes)

## Performance Considerations

- Queries are optimized with proper filtering
- Data is cached via React Query
- Lazy loading of analytics data
- Efficient calculations using existing calculators

## Future Enhancements

Potential additions:
- Interactive charts for diversification visualization
- Tax-loss harvesting opportunities
- Rebalancing recommendations
- Correlation analysis between holdings
- Sector/industry breakdown
- Geographic diversification analysis
