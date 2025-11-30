import { useState, useEffect } from 'react';
import { InvoiceForm } from './InvoiceForm';
import { Invoice } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Users } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { approvalApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

interface InvoiceFormWithApprovalProps {
  invoice?: Invoice;
  isEdit?: boolean;
  onInvoiceUpdate?: (updatedInvoice: Invoice) => void;
  initialData?: any;
  attachment?: File | null;
  prefillNewClient?: { name?: string; email?: string; address?: string; phone?: string } | null;
  openNewClientOnInit?: boolean;
}

export function InvoiceFormWithApproval({
  invoice,
  isEdit = false,
  onInvoiceUpdate,
  initialData,
  attachment,
  prefillNewClient,
  openNewClientOnInit
}: InvoiceFormWithApprovalProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [submitForApproval, setSubmitForApproval] = useState(false);
  const [selectedApproverId, setSelectedApproverId] = useState<string>('');
  const [availableApprovers, setAvailableApprovers] = useState<Array<{ id: number; name: string; email: string }>>([]);
  const [approvalsNotLicensed, setApprovalsNotLicensed] = useState(false);

  useEffect(() => {
    const fetchApprovers = async () => {
      try {
        const response = await approvalApi.getApprovers();
        setAvailableApprovers(response);
        setApprovalsNotLicensed(false);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        // Check if it's a license error (402 Payment Required)
        if (errorMessage.includes('not included in your current license') || errorMessage.includes('requires a valid license')) {
          setApprovalsNotLicensed(true);
          setAvailableApprovers([]);
        } else {
          console.error('Failed to fetch approvers:', error);
          setAvailableApprovers([]);
        }
      }
    };
    fetchApprovers();
  }, []);

  const handleInvoiceUpdate = async (updatedInvoice: Invoice) => {
    // Call the original callback if provided
    if (onInvoiceUpdate) {
      onInvoiceUpdate(updatedInvoice);
    }

    // If approval is requested, submit the invoice for approval
    if (submitForApproval && selectedApproverId && !approvalsNotLicensed) {
      try {
        await approvalApi.submitInvoiceForApproval(updatedInvoice.id, {
          approver_id: parseInt(selectedApproverId),
          notes: undefined
        });
        // Show success message
        const { toast } = await import('sonner');
        toast.success(t('invoices.submitted_for_approval', 'Invoice submitted for approval'));
      } catch (error) {
        console.error('Failed to submit invoice for approval:', error);
        const { toast } = await import('sonner');
        toast.error(t('invoices.failed_to_submit_for_approval', 'Failed to submit invoice for approval'));
      }
    }
  };

  return (
    <>
      <InvoiceForm
        invoice={invoice}
        isEdit={isEdit}
        onInvoiceUpdate={handleInvoiceUpdate}
        initialData={initialData}
        attachment={attachment}
        prefillNewClient={prefillNewClient}
        openNewClientOnInit={openNewClientOnInit}
      />

      <div className="w-full px-6 py-6">
        <Card>
          <CardHeader>
            <CardTitle>{t('invoices.approval_workflow', 'Approval Workflow')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="submit-for-approval"
                checked={submitForApproval}
                onCheckedChange={(checked) => setSubmitForApproval(checked as boolean)}
              />
              <label
                htmlFor="submit-for-approval"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                {isEdit 
                  ? t('invoices.submit_this_invoice_for_approval', 'Submit this invoice for approval')
                  : t('invoices.submit_this_invoice_for_approval_after_creation', 'Submit this invoice for approval after creation')}
              </label>
            </div>
            {submitForApproval && (
              <div className="mt-3 space-y-3">
                {approvalsNotLicensed ? (
                  <Alert className="border-amber-200 bg-amber-50">
                    <AlertCircle className="h-4 w-4 text-amber-600" />
                    <AlertDescription className="text-amber-800">
                      {t('common.feature_not_licensed', { 
                        defaultValue: 'Approval workflows require a commercial license. Please upgrade your license to use this feature.' 
                      })}
                    </AlertDescription>
                  </Alert>
                ) : (
                  <>
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-sm text-blue-700">
                        {t('invoices.this_invoice_will_be_submitted_for_approval', 'This invoice will be submitted for approval')}
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="approver-select" className="flex items-center gap-2 text-sm font-medium">
                        <Users className="h-4 w-4" />
                        {t('invoices.select_approver', 'Select Approver')} *
                      </Label>
                      <Select value={selectedApproverId} onValueChange={setSelectedApproverId}>
                        <SelectTrigger>
                          <SelectValue placeholder={t('invoices.choose_an_approver', 'Choose an approver')} />
                        </SelectTrigger>
                        <SelectContent>
                          {availableApprovers.map((approver) => (
                            <SelectItem key={approver.id} value={approver.id.toString()}>
                              {approver.name} ({approver.email})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
