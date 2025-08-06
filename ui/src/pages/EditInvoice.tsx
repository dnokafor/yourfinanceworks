import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { InvoiceForm } from "@/components/invoices/InvoiceForm";
import { invoiceApi, Invoice, getErrorMessage } from "@/lib/api";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { useTranslation } from 'react-i18next';

const EditInvoice = () => {
  const { t } = useTranslation();
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
        console.log("🔍 EDIT INVOICE - About to fetch invoice", parseInt(id));
        const data = await invoiceApi.getInvoice(parseInt(id));
        console.log("🔍 EDIT INVOICE - Raw API response:", JSON.stringify(data, null, 2));
        console.log("🔍 EDIT INVOICE - Loaded invoice data:", data);
        console.log("🔍 EDIT INVOICE - Attachment data:", {
          has_attachment: data.has_attachment,
          attachment_filename: data.attachment_filename,
          attachment_path: data.attachment_path
        });
        
        // Check if items exists and has content
        if (!data.items || !Array.isArray(data.items) || data.items.length === 0) {
          console.warn("Invoice items are missing or empty:", data.items);
          toast.warning(t('invoices.invoiceItemsMissing'));
        }
        
        setInvoice(data);
      } catch (error) {
        console.error("Failed to fetch invoice:", error);
        toast.error(getErrorMessage(error, t));
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchInvoice();
  }, [id, navigate, t]);

  if (loading) {
    return (
      <AppLayout>
        <div className="h-full flex justify-center items-center">
          <Loader2 className="h-8 w-8 animate-spin mr-2" />
          <p>{t('editInvoice.loadingInvoiceData')}</p>
        </div>
      </AppLayout>
    );
  }

  if (error || !invoice) {
    return (
      <AppLayout>
        <div className="h-full space-y-6 fade-in">
          <div>
            <h1 className="text-3xl font-bold">{t('editInvoice.invoiceNotFound')}</h1>
            <p className="text-muted-foreground">{t('editInvoice.invoiceNotFoundDescription')}</p>
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
          <h1 className="text-3xl font-bold">{t('editInvoice.editInvoice')}</h1>
          <p className="text-muted-foreground">{t('editInvoice.updateInvoiceDetails')}</p>
        </div>
        
        <InvoiceForm 
          invoice={invoice} 
          isEdit={true} 
          key={`${invoice.id}-${invoice.has_attachment}-${invoice.attachment_filename}`} 
          onInvoiceUpdate={(updatedInvoice) => {
            console.log("🔍 EDIT INVOICE - Invoice updated via callback:", updatedInvoice);
            console.log("🔍 EDIT INVOICE - Updated attachment info:", {
              has_attachment: updatedInvoice.has_attachment,
              attachment_filename: updatedInvoice.attachment_filename,
              attachment_path: updatedInvoice.attachment_path
            });
            setInvoice(updatedInvoice);
          }}
        />
      </div>
    </AppLayout>
  );
};

export default EditInvoice; 