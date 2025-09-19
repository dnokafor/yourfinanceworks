import React from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { InvoiceForm } from "@/components/invoices/InvoiceForm";
import { useTranslation } from "react-i18next";

const NewInvoiceManual = () => {
  const { t } = useTranslation();

  return (
    <AppLayout>
      <div className="h-full space-y-6 fade-in">
        <div>
          <h1 className="text-3xl font-bold">{t("invoices.new_invoice")}</h1>
          <p className="text-muted-foreground">Enter invoice details manually</p>
        </div>
        
        <div className="slide-in">
          <InvoiceForm />
        </div>
      </div>
    </AppLayout>
  );
};

export default NewInvoiceManual;