import React, { useState, useEffect } from "react";
import { Upload, FileText, Loader2, AlertCircle, Package } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import { apiRequest } from "@/lib/api";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { FeatureGate } from "@/components/FeatureGate";

interface InvoiceCreationChoiceProps {
  onManualCreate: (attachment?: File) => void;
  onPdfImport: (pdfData: any, pdfFile: File) => void;
  onInventoryCreate?: () => void;
}

export function InvoiceCreationChoice({ onManualCreate, onPdfImport, onInventoryCreate }: InvoiceCreationChoiceProps) {
  const { t } = useTranslation();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [processing, setProcessing] = useState(false);
  const [llmStatus, setLlmStatus] = useState<{ configured: boolean; config_source: string; message: string } | null>(null);
  const [manualAttachment, setManualAttachment] = useState<File | null>(null);


  const checkLlmConfiguration = async () => {
    try {
      const response = await apiRequest<{ configured: boolean; config_source: string; message: string }>('/invoices/ai-status');
      return response;
    } catch (error) {
      console.error('Failed to check LLM configuration:', error);
      return { configured: false, config_source: 'none', message: 'Failed to check configuration' };
    }
  };

  // Check AI status on component mount and log to console
  useEffect(() => {
    const checkInitialStatus = async () => {
      const status = await checkLlmConfiguration();
      console.log('AI Status:', status);
      setLlmStatus(status);
    };
    checkInitialStatus();
  }, []);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>, isManual = false) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      if (isManual) {
        setManualAttachment(file);
      } else {
        setSelectedFile(file);
      }
    } else {
      toast.error(t('invoices.please_select_pdf_file'));
    }
  };

  const processPdfImport = async () => {
    if (!selectedFile) return;

    setProcessing(true);

    // Add processing notification
    const addNotification = (window as any).addAINotification;
    const notificationId = addNotification?.('processing', t('invoices.processing_invoice_pdf'), t('invoices.analyzing_with_ai', { fileName: selectedFile.name }));

    try {
      // Check LLM configuration status
      const status = await checkLlmConfiguration();
      console.log('PDF Processing - AI Status:', status);
      setLlmStatus(status);

      // Upload PDF and get task_id
      const formData = new FormData();
      formData.append('pdf_file', selectedFile);

      const uploadResponse = await apiRequest<any>('/invoices/process-pdf', {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.success || !uploadResponse.task_id) {
        throw new Error(uploadResponse.message || 'Failed to queue PDF for processing');
      }

      const taskId = uploadResponse.task_id;
      console.log('PDF queued for processing, task_id:', taskId);

      // Poll for processing status
      const maxAttempts = 60; // 3 minutes with 3-second intervals
      let attempts = 0;

      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds

        try {
          const statusResponse = await apiRequest<any>(`/invoices/process-status/${taskId}`);
          console.log('Processing status:', statusResponse.status);

          if (statusResponse.status === 'completed') {
            // Success! Extract the data
            addNotification?.('success', t('invoices.invoice_pdf_processed'), t('invoices.successfully_extracted_data', { fileName: selectedFile.name }));
            toast.success(t('invoices.pdf_processed_successfully'));

            const payload = statusResponse.data?.invoice_data || statusResponse.data;
            onPdfImport(payload, selectedFile);
            return;
          } else if (statusResponse.status === 'failed') {
            throw new Error(statusResponse.error || 'Processing failed');
          }

          // Still processing, continue polling
          attempts++;
        } catch (pollError) {
          console.error('Error polling status:', pollError);
          attempts++;
        }
      }

      // Timeout
      throw new Error('Processing timeout - please try again');

    } catch (error) {
      console.error('PDF processing error:', error);
      // Update notification to error
      addNotification?.('error', t('invoices.pdf_processing_failed'), t('invoices.failed_to_process_file', { fileName: selectedFile.name, error: error instanceof Error ? error.message : 'Unknown error' }));
      toast.error(t('invoices.failed_to_process_pdf_proceeding_manual'));
      onManualCreate(selectedFile);
    } finally {
      setProcessing(false);
    }
  };

  const handleManualCreate = () => {
    onManualCreate(manualAttachment || undefined);
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold">{t('invoices.create_new_invoice')}</h2>
        <p className="text-muted-foreground">{t('invoices.choose_creation_method')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* PDF Import Option */}
        <FeatureGate feature="ai_invoice">
          <Card className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <Upload className="w-8 h-8 text-blue-600" />
              </div>
              <CardTitle className="text-xl">{t('invoices.import_from_pdf')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground text-center">
                {t('invoices.upload_pdf_to_extract_invoice_details')}
              </p>

              <div className="space-y-3">
                <div>
                  <Label htmlFor="pdf-upload">{t('invoices.select_pdf_file')}</Label>
                  <Input
                    id="pdf-upload"
                    type="file"
                    accept=".pdf"
                    onChange={(e) => handleFileSelect(e)}
                    className="cursor-pointer"
                  />
                </div>

                {selectedFile && (
                  <div className="text-sm text-green-600 bg-green-50 p-2 rounded">
                    {t('invoices.selected_file')}: {selectedFile.name}
                  </div>
                )}

                <Button
                  onClick={processPdfImport}
                  disabled={!selectedFile || processing}
                  className="w-full"
                >
                  {processing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {processing ? t('invoices.processing_pdf') : t('invoices.import_from_pdf')}
                </Button>
              </div>
            </CardContent>
          </Card>
        </FeatureGate>

        {/* Manual Creation Option */}
        <Card className="cursor-pointer hover:shadow-lg transition-shadow">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <FileText className="w-8 h-8 text-green-600" />
            </div>
            <CardTitle className="text-xl">{t('invoices.create_manually')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground text-center">
              {t('invoices.quick_create_guided_create_manual_description')}
            </p>

            <div className="space-y-3">
              <div>
                <Label htmlFor="manual-attachment">{t('invoices.optional_attachment')}</Label>
                <Input
                  id="manual-attachment"
                  type="file"
                  accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                  onChange={(e) => handleFileSelect(e, true)}
                  className="cursor-pointer"
                />
              </div>

              {manualAttachment && (
                <div className="text-sm text-green-600 bg-green-50 p-2 rounded">
                  {t('invoices.attachment_selected')}: {manualAttachment.name}
                </div>
              )}

              <Button
                onClick={handleManualCreate}
                className="w-full"
                variant="outline"
              >
                {t('invoices.create_manually')}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Inventory Integration Option */}
        {onInventoryCreate && (
          <Card className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-4">
                <Package className="w-8 h-8 text-purple-600" />
              </div>
              <CardTitle className="text-xl">{t('invoices.create_with_inventory')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground text-center">
                {t('invoices.inventory_catalog_description')}
              </p>

              <div className="space-y-3">
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-purple-800">
                    <Package className="w-4 h-4" />
                    <span className="text-sm font-medium">{t('invoices.features')}</span>
                  </div>
                  <ul className="text-sm text-purple-700 mt-2 space-y-1">
                    <li>• {t('invoices.select_from_inventory_catalog')}</li>
                    <li>• {t('invoices.automatic_stock_validation')}</li>
                    <li>• {t('invoices.real_time_pricing_updates')}</li>
                    <li>• {t('invoices.low_stock_warnings')}</li>
                  </ul>
                </div>

                <Button
                  onClick={onInventoryCreate}
                  className="w-full bg-purple-600 hover:bg-purple-700"
                >
                  <Package className="w-4 h-4 mr-2" />
                  {t('invoices.create_with_inventory')}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}