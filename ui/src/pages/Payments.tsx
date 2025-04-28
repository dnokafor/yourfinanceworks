import { useState, useEffect } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Loader2 } from "lucide-react";
import { paymentApi, Payment } from "@/lib/api";
import { toast } from "sonner";

const Payments = () => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPayments = async () => {
      setLoading(true);
      try {
        const data = await paymentApi.getPayments();
        setPayments(data);
      } catch (error) {
        console.error("Failed to fetch payments:", error);
        toast.error("Failed to load payments");
      } finally {
        setLoading(false);
      }
    };
    
    fetchPayments();
  }, []);

  // Calculate payment statistics
  const totalReceived = payments.reduce((total, payment) => total + payment.amount, 0);
  const averagePayment = payments.length > 0 ? totalReceived / payments.length : 0;

  return (
    <AppLayout>
      <div className="h-full space-y-6 fade-in">
        <div>
          <h1 className="text-3xl font-bold">Payments</h1>
          <p className="text-muted-foreground">Track payments received from clients</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 slide-in">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Received</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${totalReceived.toFixed(2)}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Payments This Month</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {payments.length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Average Payment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${averagePayment.toFixed(2)}
              </div>
            </CardContent>
          </Card>
        </div>
        
        <Card className="slide-in" style={{ animationDelay: '100ms' }}>
          <CardHeader>
            <CardTitle>Payment History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Invoice</TableHead>
                    <TableHead>Client</TableHead>
                    <TableHead>Method</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={5} className="h-24 text-center">
                        <div className="flex justify-center items-center">
                          <Loader2 className="h-6 w-6 animate-spin mr-2" />
                          Loading payments...
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : payments.length > 0 ? (
                    payments.map((payment) => (
                      <TableRow key={payment.id}>
                        <TableCell>{payment.date}</TableCell>
                        <TableCell className="font-medium">{payment.invoice_number}</TableCell>
                        <TableCell>{payment.client_name}</TableCell>
                        <TableCell>{payment.method}</TableCell>
                        <TableCell className="text-right font-medium text-green-600">
                          ${payment.amount.toFixed(2)}
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} className="h-24 text-center">
                        No payments found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
};

export default Payments;
