import { useState, useEffect } from "react";
import { BarChart, DollarSign, FileText, Users } from "lucide-react";
import { StatCard } from "@/components/dashboard/StatCard";
import { RecentInvoices } from "@/components/dashboard/RecentInvoices";
import { InvoiceChart } from "@/components/dashboard/InvoiceChart";
import { AppLayout } from "@/components/layout/AppLayout";
import { dashboardApi } from "@/lib/api";
import { toast } from "sonner";

const Dashboard = () => {
  const [dashboardStats, setDashboardStats] = useState({
    totalIncome: 0,
    pendingInvoices: 0,
    totalClients: 0,
    invoicesPaid: 0,
    invoicesPending: 0,
    invoicesOverdue: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardStats = async () => {
      setLoading(true);
      try {
        const stats = await dashboardApi.getStats();
        setDashboardStats(stats);
      } catch (error) {
        console.error("Failed to fetch dashboard stats:", error);
        toast.error("Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };
    
    fetchDashboardStats();
  }, []);

  return (
    <AppLayout>
      <div className="h-full space-y-6 fade-in">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Overview of your invoicing activity</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 slide-in">
          <StatCard
            title="Total Income"
            value={`$${dashboardStats.totalIncome.toFixed(2)}`}
            icon={DollarSign}
            description="Revenue from paid invoices"
            trend={{ value: 12.5, isPositive: true }}
            loading={loading}
          />
          <StatCard
            title="Pending Amount"
            value={`$${dashboardStats.pendingInvoices.toFixed(2)}`}
            icon={FileText}
            description="Awaiting payment"
            trend={{ value: 5.2, isPositive: true }}
            loading={loading}
          />
          <StatCard
            title="Total Clients"
            value={dashboardStats.totalClients.toString()}
            icon={Users}
            description="Active client accounts"
            trend={{ value: 0, isPositive: true }}
            loading={loading}
          />
          <StatCard
            title="Overdue Invoices"
            value={dashboardStats.invoicesOverdue.toString()}
            icon={FileText}
            description="Invoices past due date"
            trend={{ value: 2.5, isPositive: false }}
            loading={loading}
          />
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 slide-in" style={{ animationDelay: '100ms' }}>
          <InvoiceChart />
          <RecentInvoices />
        </div>
      </div>
    </AppLayout>
  );
};

export default Dashboard;
