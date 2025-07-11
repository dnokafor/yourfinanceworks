import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Loader2 } from "lucide-react";
import { invoiceApi, Invoice } from "@/lib/api";
import { toast } from "sonner";

export function InvoiceChart() {
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInvoices = async () => {
      setLoading(true);
      try {
        const data = await invoiceApi.getInvoices();
        console.log('Fetched invoices for chart:', data);
        prepareChartData(data);
      } catch (error) {
        console.error("Failed to fetch invoices for chart:", error);
        toast.error("Failed to load invoice data for chart");
      } finally {
        setLoading(false);
      }
    };
    
    fetchInvoices();
  }, []);

  const prepareChartData = (invoiceData: Invoice[]) => {
    console.log('Preparing chart data for invoices:', invoiceData);
    const chartDataMap = new Map<string, { paid: number; pending: number; partiallyPaid: number }>();

    // Initialize chart data for the last 6 months
    for (let i = 0; i < 6; i++) {
      const month = new Date();
      month.setMonth(month.getMonth() - 5 + i);
      const monthName = month.toLocaleString('default', { month: 'short' });
      const year = month.getFullYear().toString().slice(2);
      const label = `${monthName} '${year}`;
      chartDataMap.set(label, { paid: 0, pending: 0, partiallyPaid: 0 });
    }

    invoiceData.forEach(invoice => {
      const invoiceDate = new Date(invoice.date || invoice.created_at);
      if (isNaN(invoiceDate.getTime())) return;

      const month = new Date(invoiceDate.getFullYear(), invoiceDate.getMonth(), 1);
      const monthName = month.toLocaleString('default', { month: 'short' });
      const year = month.getFullYear().toString().slice(2);
      const label = `${monthName} '${year}`;

      if (chartDataMap.has(label)) {
        const currentData = chartDataMap.get(label)!;
        if (invoice.status === 'paid') {
          currentData.paid += invoice.amount;
        } else if (invoice.status === 'partially_paid') {
          currentData.partiallyPaid += (invoice.paid_amount || 0);
          currentData.pending += (invoice.amount - (invoice.paid_amount || 0));
        } else if (invoice.status === 'pending' || invoice.status === 'overdue') {
          currentData.pending += invoice.amount;
        }
        chartDataMap.set(label, currentData);
      }
    });

    const finalChartData = Array.from(chartDataMap.entries()).map(([name, data]) => ({
      name,
      paid: parseFloat(data.paid.toFixed(2)),
      pending: parseFloat(data.pending.toFixed(2)),
      partiallyPaid: parseFloat(data.partiallyPaid.toFixed(2)),
    }));
    
    setChartData(finalChartData);
  };

  return (
    <Card className="col-span-2 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader>
        <CardTitle>Invoice Overview</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-[300px] flex justify-center items-center">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        ) : (
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{
                  top: 5,
                  right: 30,
                  left: 20,
                  bottom: 25,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #e0e0e0",
                    borderRadius: "6px",
                    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
                  }}
                  formatter={(value, name, props) => {
                  let categoryName = '';
                  if (props.dataKey === 'paid') {
                    categoryName = 'Paid';
                  } else if (props.dataKey === 'partiallyPaid') {
                    categoryName = 'Partially Paid';
                  } else if (props.dataKey === 'pending') {
                    categoryName = 'Pending';
                  } else {
                    categoryName = name; // Fallback
                  }
                  return [`${value}`, categoryName];
                }}
                />
                <Bar dataKey="paid" name="Paid" fill="#38bdf8" radius={[4, 4, 0, 0]} stackId="a" />
                <Bar dataKey="partiallyPaid" name="Partially Paid" fill="#fbbf24" radius={[4, 4, 0, 0]} stackId="a" />
                <Bar dataKey="pending" name="Pending" fill="#60a5fa" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
