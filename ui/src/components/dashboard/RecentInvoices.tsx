import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
import { invoiceApi, Invoice } from "@/lib/api";
import { toast } from "sonner";
import { CurrencyDisplay } from "@/components/ui/currency-display";

export function RecentInvoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInvoices = async () => {
      setLoading(true);
      try {
        const data = await invoiceApi.getInvoices();
        console.log('[DEBUG] Invoices received from API:', data);
        // Sort by date and take only the most recent 5
        const sortedInvoices = [...data]
          .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
          .slice(0, 5);
        console.log('[DEBUG] Sorted invoices for display:', sortedInvoices);
        setInvoices(sortedInvoices);
      } catch (error) {
        console.error("Failed to fetch recent invoices:", error);
        toast.error("Failed to load recent invoices");
      } finally {
        setLoading(false);
      }
    };
    
    fetchInvoices();
  }, []);

  return (
    <Card className="col-span-1 shadow-sm hover:shadow-md transition-shadow h-full">
      <CardHeader>
        <CardTitle>Recent Invoices</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center items-center h-48">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Invoice</TableHead>
                <TableHead>Client</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoices.length > 0 ? (
                invoices.map((invoice) => {
                  console.log('[DEBUG] Rendering invoice row:', invoice);
                  return (
                    <TableRow key={invoice.id}>
                      <TableCell className="font-medium">{invoice.number}</TableCell>
                      <TableCell>{invoice.client_name}</TableCell>
                      <TableCell>
                        <CurrencyDisplay amount={invoice.amount} currency={invoice.currency} />
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant={
                            invoice.status === 'paid' ? 'default' : 
                            invoice.status === 'pending' ? 'secondary' : 
                            'destructive'
                          }
                          className={
                            invoice.status === 'paid' ? 'bg-green-100 text-green-800 hover:bg-green-100' : 
                            invoice.status === 'pending' ? 'bg-orange-100 text-orange-800 hover:bg-orange-100' : 
                            'bg-red-100 text-red-800 hover:bg-red-100'
                          }
                        >
                          {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })
              ) : (
                console.log('[DEBUG] No invoices to render, invoices array is empty'),
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-6">
                    No invoices found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
