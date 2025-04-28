
import { AppLayout } from "@/components/layout/AppLayout";
import { InvoiceForm } from "@/components/invoices/InvoiceForm";

const NewInvoice = () => {
  return (
    <AppLayout>
      <div className="h-full space-y-6 fade-in">
        <div>
          <h1 className="text-3xl font-bold">New Invoice</h1>
          <p className="text-muted-foreground">Create a new invoice for your clients</p>
        </div>
        
        <div className="slide-in">
          <InvoiceForm />
        </div>
      </div>
    </AppLayout>
  );
};

export default NewInvoice;
