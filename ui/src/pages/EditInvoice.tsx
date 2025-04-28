import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { InvoiceForm } from "@/components/invoices/InvoiceForm";
import { invoiceApi, Invoice } from "@/lib/api";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

const EditInvoice = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchInvoice = async () => {
      if (!id) {
        navigate("/invoices");
        return;
      }

      setLoading(true);
      try {
        const data = await invoiceApi.getInvoice(parseInt(id));
        console.log("Loaded invoice data:", data);
        
        // Check if items exists and has content
        if (!data.items || !Array.isArray(data.items) || data.items.length === 0) {
          console.warn("Invoice items are missing or empty:", data.items);
          toast.warning("Invoice items could not be loaded properly");
        }
        
        setInvoice(data);
      } catch (error) {
        console.error("Failed to fetch invoice:", error);
        toast.error("Failed to load invoice data");
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchInvoice();
  }, [id, navigate]);

  if (loading) {
    return (
      <AppLayout>
        <div className="h-full flex justify-center items-center">
          <Loader2 className="h-8 w-8 animate-spin mr-2" />
          <p>Loading invoice data...</p>
        </div>
      </AppLayout>
    );
  }

  if (error || !invoice) {
    return (
      <AppLayout>
        <div className="h-full space-y-6 fade-in">
          <div>
            <h1 className="text-3xl font-bold">Invoice Not Found</h1>
            <p className="text-muted-foreground">The invoice you're looking for doesn't exist or couldn't be loaded.</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  // Make sure invoice has an items array even if API didn't return one
  if (!invoice.items) {
    invoice.items = [];
  }

  return (
    <AppLayout>
      <div className="h-full space-y-6 fade-in">
        <div>
          <h1 className="text-3xl font-bold">Edit Invoice</h1>
          <p className="text-muted-foreground">Update invoice details</p>
        </div>
        
        <InvoiceForm invoice={invoice} isEdit={true} />
      </div>
    </AppLayout>
  );
};

export default EditInvoice; 