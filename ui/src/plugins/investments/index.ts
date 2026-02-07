/**
 * Investment Management Plugin
 *
 * This plugin provides comprehensive investment portfolio management capabilities
 * including holdings tracking, performance analytics, and tax reporting.
 */

// Export pages
export { default as InvestmentDashboard } from '@/pages/investments/InvestmentDashboard';
export { default as CreatePortfolio } from '@/pages/investments/CreatePortfolio';
export { default as PortfolioDetail } from '@/pages/investments/PortfolioDetail';

// Export components
export { default as HoldingsList } from '@/components/investments/HoldingsList';
export { default as CreateHoldingDialog } from '@/components/investments/CreateHoldingDialog';
export { default as EditHoldingDialog } from '@/components/investments/EditHoldingDialog';

// Plugin metadata
export const pluginMetadata = {
  name: 'investments',
  displayName: 'Investment Management',
  version: '1.0.0',
  licenseTier: 'commercial',
  description: 'Comprehensive investment portfolio management with holdings tracking, performance analytics, and tax reporting',
};

// Plugin routes configuration
export const pluginRoutes = [
  {
    path: '/investments',
    component: 'InvestmentDashboard',
    label: 'Investment Dashboard',
  },
  {
    path: '/investments/portfolio/new',
    component: 'CreatePortfolio',
    label: 'Create Portfolio',
  },
  {
    path: '/investments/portfolio/:id',
    component: 'PortfolioDetail',
    label: 'Portfolio Details',
  },
];

// Plugin features
export const pluginFeatures = [
  'portfolio-management',
  'holdings-tracking',
  'transaction-recording',
  'performance-analytics',
  'asset-allocation',
  'dividend-tracking',
  'tax-reporting',
  'price-management',
];

// Plugin permissions
export const pluginPermissions = [
  'investments:read',
  'investments:create',
  'investments:update',
  'investments:delete',
];
