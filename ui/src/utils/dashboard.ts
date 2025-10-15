/**
 * Dashboard utility functions
 */

/**
 * Triggers a dashboard refresh event that components can listen to
 * This is useful when data is created/updated in other parts of the app
 * and the dashboard needs to refresh its data
 */
export function refreshDashboard() {
  // Dispatch a custom event that the dashboard can listen to
  window.dispatchEvent(new CustomEvent('dashboard-refresh'));
}

/**
 * Triggers a refresh of recent activity specifically
 */
export function refreshRecentActivity() {
  window.dispatchEvent(new CustomEvent('recent-activity-refresh'));
}

/**
 * Triggers a refresh of recent invoices specifically
 */
export function refreshRecentInvoices() {
  window.dispatchEvent(new CustomEvent('recent-invoices-refresh'));
}

/**
 * Triggers a refresh of dashboard stats
 */
export function refreshDashboardStats() {
  window.dispatchEvent(new CustomEvent('dashboard-stats-refresh'));
}
/**
 * 
Helper functions to log activities and trigger dashboard refresh
 * These can be called from other parts of the app when actions are performed
 */

/**
 * Log a new invoice creation and refresh dashboard
 */
export function logInvoiceActivity(invoiceNumber: string, clientName: string) {
  // In a real implementation, this would send the activity to the backend
  console.log(`Activity logged: Invoice ${invoiceNumber} created for ${clientName}`);
  refreshDashboard();
}

/**
 * Log a new client creation and refresh dashboard
 */
export function logClientActivity(clientName: string) {
  console.log(`Activity logged: New client ${clientName} added`);
  refreshDashboard();
}

/**
 * Log an expense approval and refresh dashboard
 */
export function logApprovalActivity(expenseType: string, amount: number, status: string) {
  console.log(`Activity logged: ${expenseType} expense ${status} for $${amount}`);
  refreshDashboard();
}

/**
 * Log a reminder sent and refresh dashboard
 */
export function logReminderActivity(type: string, target: string) {
  console.log(`Activity logged: ${type} reminder sent to ${target}`);
  refreshDashboard();
}

/**
 * Log a report generation and refresh dashboard
 */
export function logReportActivity(reportType: string, period: string) {
  console.log(`Activity logged: ${reportType} report generated for ${period}`);
  refreshDashboard();
}