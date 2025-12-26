import React from "react";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@/components/ui/theme-provider";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { RoleProtectedRoute } from "./components/auth/RoleProtectedRoute";
import { TenantProtectedRoute } from "./components/auth/TenantProtectedRoute";
import Index from "./pages/Index";
import Login from "./pages/Login";
import OAuthCallback from "./pages/OAuthCallback";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Clients from "./pages/Clients";
import NewClient from "./pages/NewClient";
import EditClient from "./pages/EditClient";
import Invoices from "./pages/Invoices";
import NewInvoice from "./pages/NewInvoice";
import NewInvoiceManual from "./pages/NewInvoiceManual";
import EditInvoice from "./pages/EditInvoice";
import ViewInvoice from "./pages/ViewInvoice";
import Payments from "./pages/Payments";
import ExpensesNew from "./pages/ExpensesNew";
import ExpensesImport from "./pages/ExpensesImport";
import ExpensesEdit from "./pages/ExpensesEdit";
import ExpensesView from "./pages/ExpensesView";
import Expenses from "./pages/Expenses";
import Statements from "./pages/Statements";
import Settings from "./pages/Settings";
import Users from "./pages/Users";
import SuperAdmin from "./pages/SuperAdmin";
import NotFound from "./pages/NotFound";
import AIAssistant from "./components/AIAssistant";
import { Toaster } from "sonner";
import AuditLog from "./pages/AuditLog";
import RecycleBin from "./pages/RecycleBin";
import ExpenseRecycleBin from "./pages/ExpenseRecycleBin";
import StatementRecycleBin from "./pages/StatementRecycleBin";
import Analytics from "./pages/Analytics";
import Reports from "./pages/Reports";
import ReportDetail from "./pages/ReportDetail";
import AttachmentSearch from "./pages/AttachmentSearch";
import { ActivityPage } from "./pages/ActivityPage";
import { NotificationBell } from "./components/notifications/NotificationBell";
import { useNotifications } from "./hooks/useNotifications";
import { useExpenseStatusPolling } from "./hooks/useExpenseStatusPolling";
import { useJoinRequestPolling } from "./hooks/useJoinRequestPolling";
import { getCurrentUser } from "./utils/auth";
import { Favicon } from "./components/ui/favicon";
import { useQuery } from "@tanstack/react-query";
import { settingsApi } from "@/lib/api";
import { isAdmin } from "@/utils/auth";
import { OnboardingProvider } from "./components/onboarding/OnboardingProvider";
import { TourOverlay } from "./components/onboarding/TourOverlay";
import { SearchProvider } from "./components/search/SearchProvider";
import { SearchDialog } from "./components/search/SearchDialog";
import { FeatureProvider } from "./contexts/FeatureContext";

import Inventory from "./pages/Inventory";
import NewInventoryItem from "./pages/NewInventoryItem";
import EditInventoryItem from "./pages/EditInventoryItem";
import InventoryItemDetail from "./pages/InventoryItemDetail";
import NewInventoryInvoice from "./pages/NewInventoryInvoice";
import { ApprovalDashboard } from "./components/approvals/ApprovalDashboard";
import ApprovalReportsPage from "./pages/ApprovalReportsPage";
import Reminders from "./pages/Reminders";
import { AppLayout } from "./components/layout/AppLayout";
import { AuthenticatedLayout } from "./components/layout/AuthenticatedLayout";
import OrganizationJoinRequests from "./pages/OrganizationJoinRequests";
import PromptManagement from "./pages/PromptManagement";
import Gamification from "./pages/Gamification";



const queryClient = new QueryClient();

const AppContent = () => {
  const { notifications, addNotification, markAsRead, clearAll } = useNotifications();
  const { startPolling } = useExpenseStatusPolling();
  const [bellHidden, setBellHidden] = React.useState(false);
  const isLoggedIn = getCurrentUser() !== null;
  const currentUser = getCurrentUser();
  const userIsAdmin = currentUser?.role === 'admin';

  // Poll for new join requests if user is admin
  useJoinRequestPolling(userIsAdmin, addNotification);

  // Get company branding for favicon
  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsApi.getSettings(),
    enabled: isLoggedIn && isAdmin(),
    retry: false,
  });

  // Make notification functions available globally
  React.useEffect(() => {
    (window as any).addAINotification = addNotification;
    (window as any).startExpensePolling = startPolling;
  }, [addNotification, startPolling]);

  // Show bell again when new notifications arrive
  React.useEffect(() => {
    if (notifications.length > 0 && notifications.some(n => !n.read)) {
      setBellHidden(false);
    }
  }, [notifications]);

  return (
    <TooltipProvider>
      <Favicon
        logoUrl={settings?.company_info?.logo}
        companyName={settings?.company_info?.name}
      />

      <BrowserRouter>
        <FeatureProvider>
          <SearchProvider>
            <OnboardingProvider>

              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/oauth-callback" element={<OAuthCallback />} />
                <Route path="/signup" element={<Signup />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password" element={<ResetPassword />} />
                <Route element={<ProtectedRoute><AuthenticatedLayout /></ProtectedRoute>}>
                  <Route path="/" element={<Index />} />
                  <Route path="/dashboard" element={<Index />} />
                  <Route path="/clients" element={<Clients />} />
                  <Route path="/clients/new" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><NewClient /></RoleProtectedRoute>} />
                  <Route path="/clients/edit/:id" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><EditClient /></RoleProtectedRoute>} />
                  <Route path="/invoices" element={<Invoices />} />
                  <Route path="/invoices/new" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><NewInvoice /></RoleProtectedRoute>} />
                  <Route path="/invoices/new-manual" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><NewInvoiceManual /></RoleProtectedRoute>} />
                  <Route path="/invoices/view/:id" element={<ViewInvoice />} />
                  <Route path="/invoices/edit/:id" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><EditInvoice /></RoleProtectedRoute>} />
                  <Route path="/payments" element={<Payments />} />
                  <Route path="/expenses/new" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><ExpensesNew /></RoleProtectedRoute>} />
                  <Route path="/expenses/import" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><ExpensesImport /></RoleProtectedRoute>} />
                  <Route path="/expenses/view/:id" element={<ExpensesView />} />
                  <Route path="/expenses/edit/:id" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><ExpensesEdit /></RoleProtectedRoute>} />
                  <Route path="/expenses" element={<Expenses />} />
                  <Route path="/reminders" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><Reminders /></RoleProtectedRoute>} />
                  <Route path="/approvals" element={<ApprovalDashboard />} />
                  <Route path="/approvals/reports" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><ApprovalReportsPage /></RoleProtectedRoute>} />
                  <Route path="/statements" element={<Statements />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/users" element={<RoleProtectedRoute allowedRoles={['admin']}><Users /></RoleProtectedRoute>} />
                  <Route path="/organization-join-requests" element={<RoleProtectedRoute allowedRoles={['admin']}><OrganizationJoinRequests /></RoleProtectedRoute>} />
                  <Route path="/super-admin" element={<TenantProtectedRoute requireSuperUser={true} requirePrimaryTenant={true}><SuperAdmin /></TenantProtectedRoute>} />
                  <Route path="/audit-log" element={<RoleProtectedRoute allowedRoles={['admin', 'superuser']}><AuditLog /></RoleProtectedRoute>} />
                  <Route path="/recycle-bin" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><RecycleBin /></RoleProtectedRoute>} />
                  <Route path="/analytics" element={<RoleProtectedRoute allowedRoles={['admin', 'superuser']}><Analytics /></RoleProtectedRoute>} />
                  <Route path="/reports" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><Reports /></RoleProtectedRoute>} />
                  <Route path="/reports/:reportType" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><ReportDetail /></RoleProtectedRoute>} />
                  <Route path="/attachments" element={<AttachmentSearch />} />
                  <Route path="/activity" element={<ActivityPage />} />
                  <Route path="/inventory" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><Inventory /></RoleProtectedRoute>} />
                  <Route path="/inventory/new" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><NewInventoryItem /></RoleProtectedRoute>} />
                  <Route path="/inventory/view/:id" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><InventoryItemDetail /></RoleProtectedRoute>} />
                  <Route path="/inventory/edit/:id" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><EditInventoryItem /></RoleProtectedRoute>} />
                  <Route path="/inventory/new-inventory" element={<RoleProtectedRoute allowedRoles={['admin', 'user']}><NewInventoryInvoice /></RoleProtectedRoute>} />
                  <Route path="/prompts" element={<RoleProtectedRoute allowedRoles={['admin']}><PromptManagement /></RoleProtectedRoute>} />
                  <Route path="/recycle-bin" element={<RecycleBin />} />
                  <Route path="/expenses/recycle-bin" element={<ExpenseRecycleBin />} />
                  <Route path="/statements/recycle-bin" element={<StatementRecycleBin />} />
                </Route>
                <Route path="/" element={<ProtectedRoute><Index /></ProtectedRoute>} />
                <Route path="/dashboard" element={<ProtectedRoute><Index /></ProtectedRoute>} />
                <Route path="/clients" element={<ProtectedRoute><Clients /></ProtectedRoute>} />
                <Route path="/clients/new" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><NewClient /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/clients/edit/:id" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><EditClient /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/invoices" element={<ProtectedRoute><Invoices /></ProtectedRoute>} />
                <Route path="/invoices/new" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><NewInvoice /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/invoices/new-manual" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><NewInvoiceManual /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/invoices/view/:id" element={<ProtectedRoute><ViewInvoice /></ProtectedRoute>} />
                <Route path="/invoices/edit/:id" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><EditInvoice /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/payments" element={<ProtectedRoute><Payments /></ProtectedRoute>} />
                <Route path="/expenses/new" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><ExpensesNew /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/expenses/import" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><ExpensesImport /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/expenses/view/:id" element={<ProtectedRoute><ExpensesView /></ProtectedRoute>} />
                <Route path="/expenses/edit/:id" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><ExpensesEdit /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/expenses" element={<ProtectedRoute><Expenses /></ProtectedRoute>} />
                <Route path="/reminders" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><Reminders /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/approvals" element={<ProtectedRoute><AppLayout><ApprovalDashboard /></AppLayout></ProtectedRoute>} />
                <Route path="/approvals/reports" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><AppLayout><ApprovalReportsPage /></AppLayout></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/statements" element={<ProtectedRoute><Statements /></ProtectedRoute>} />
                <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
                <Route path="/users" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin']}><Users /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/organization-join-requests" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin']}><OrganizationJoinRequests /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/super-admin" element={<ProtectedRoute><TenantProtectedRoute requireSuperUser={true} requirePrimaryTenant={true}><SuperAdmin /></TenantProtectedRoute></ProtectedRoute>} />
                <Route path="/audit-log" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'superuser']}><AuditLog /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/recycle-bin" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><RecycleBin /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/analytics" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'superuser']}><Analytics /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/reports" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><Reports /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/reports/:reportType" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><ReportDetail /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/attachments" element={<ProtectedRoute><AttachmentSearch /></ProtectedRoute>} />
                <Route path="/activity" element={<ProtectedRoute><AppLayout><ActivityPage /></AppLayout></ProtectedRoute>} />
                <Route path="/inventory" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><Inventory /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/inventory/new" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><NewInventoryItem /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/inventory/view/:id" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><InventoryItemDetail /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/inventory/edit/:id" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><EditInventoryItem /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/inventory/new-inventory" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin', 'user']}><NewInventoryInvoice /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/prompts" element={<ProtectedRoute><RoleProtectedRoute allowedRoles={['admin']}><PromptManagement /></RoleProtectedRoute></ProtectedRoute>} />
                <Route path="/gamification" element={<ProtectedRoute><Gamification /></ProtectedRoute>} />
                <Route path="/recycle-bin" element={<ProtectedRoute><RecycleBin /></ProtectedRoute>} />
                <Route path="/expenses/recycle-bin" element={<ProtectedRoute><ExpenseRecycleBin /></ProtectedRoute>} />
                <Route path="/statements/recycle-bin" element={<ProtectedRoute><StatementRecycleBin /></ProtectedRoute>} />

                <Route path="*" element={<NotFound />} />
              </Routes>
              {isLoggedIn && !bellHidden && (
                <NotificationBell
                  notifications={notifications}
                  onMarkAsRead={markAsRead}
                  onClearAll={clearAll}
                  onHide={() => setBellHidden(true)}
                />
              )}
              {isLoggedIn && bellHidden && notifications.some(n => !n.read) && (
                <div
                  className="fixed top-4 right-4 z-50 cursor-pointer"
                  onClick={() => setBellHidden(false)}
                  title="Show AI notifications"
                >
                  <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse"></div>
                </div>
              )}
              <TourOverlay />
            </OnboardingProvider>
            <SearchDialog />
          </SearchProvider>
        </FeatureProvider>
      </BrowserRouter>

      <AIAssistant />
      <Toaster position="top-center" richColors />
    </TooltipProvider>
  );
};

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="system" storageKey="invoice-app-theme">
        <AppContent />
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
