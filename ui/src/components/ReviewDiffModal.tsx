import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Check, X, ArrowRight, AlertTriangle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { format, isValid, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';

/**
 * Safely format a date string, handling "null", "None", and other invalid inputs.
 */
const safeFormatDate = (v: any) => {
  if (!v || v === 'null' || v === 'None') return '';
  try {
    const d = typeof v === 'string' ? parseISO(v) : new Date(v);
    return isValid(d) ? format(d, 'yyyy-MM-dd') : '';
  } catch {
    return '';
  }
};

interface ReviewDiffModalProps {
  isOpen: boolean;
  onClose: () => void;
  originalData: any;
  reviewResult: any; // The review_result dictionary from backend
  onAccept: () => void;
  onReject: () => void;
  onRetrigger: () => void;
  isAccepting: boolean;
  isRejecting: boolean;
  isRetriggering: boolean;
  type: 'expense' | 'invoice' | 'statement';
}

interface DiffRowProps {
  label: string;
  originalValue: any;
  newValue: any;
  formatter?: (val: any) => string;
}

const DiffRow: React.FC<DiffRowProps> = ({ label, originalValue, newValue, formatter }) => {
  // Enhanced "effectively empty" check
  const isEffectivelyEmpty = (val: any) => {
    if (val === null || val === undefined || val === '') return true;
    if (typeof val === 'string' && (val.toLowerCase() === 'null' || val.toLowerCase() === 'none')) return true;
    // Don't treat 0 as empty if it's a number that meaningful (e.g. amount), 
    // but in many LLM outputs 0.0 is a placeholder for null
    return false;
  };

  const isDifferent = (() => {
    const empty1 = isEffectivelyEmpty(originalValue);
    const empty2 = isEffectivelyEmpty(newValue);

    // If both are empty, they are not different
    if (empty1 && empty2) return false;

    // special case for number 0 vs empty
    if ((originalValue === 0 || originalValue === 0.0) && empty2) return false;
    if (empty1 && (newValue === 0 || newValue === 0.0)) return false;

    return JSON.stringify(originalValue) !== JSON.stringify(newValue);
  })();

  // Format values
  const formatValue = (val: any) => {
    if (isEffectivelyEmpty(val)) return <span className="text-muted-foreground italic">Empty</span>;
    if (formatter) return formatter(val);
    if (typeof val === 'boolean') return val ? 'Yes' : 'No';
    if (typeof val === 'object') return JSON.stringify(val);
    return String(val);
  };

  return (
    <div className={cn("grid grid-cols-[120px_1fr_24px_1fr] gap-4 py-3 border-b text-sm items-center", 
      isDifferent ? "bg-amber-500/5 -mx-4 px-4 border-amber-500/20" : "border-border/50"
    )}>
      <div className="font-medium text-muted-foreground">{label}</div>
      <div className="break-all">{formatValue(originalValue)}</div>
      <div className="flex justify-center text-muted-foreground">
        {isDifferent ? <ArrowRight className="h-4 w-4 text-amber-500" /> : <div className="w-4" />}
      </div>
      <div className={cn("break-all font-medium", isDifferent ? "text-amber-600 dark:text-amber-400" : "")}>
        {formatValue(newValue)}
      </div>
    </div>
  );
};

export const ReviewDiffModal: React.FC<ReviewDiffModalProps> = ({
  isOpen,
  onClose,
  originalData,
  reviewResult,
  onAccept,
  onReject,
  onRetrigger,
  isAccepting,
  isRejecting,
  isRetriggering,
  type
}) => {
  const { t } = useTranslation();

  if (!reviewResult) return null;

  // Extract relevant fields based on type
  // This comparison logic mimics backend but for display
  const fields = [];

  if (type === 'expense') {
    fields.push({ key: 'amount', label: 'Amount' });
    fields.push({ key: 'currency', label: 'Currency' });
    fields.push({ key: 'expense_date', label: 'Date', altKey: 'date', formatter: safeFormatDate });
    fields.push({ key: 'category', label: 'Category' });
    fields.push({ key: 'vendor', label: 'Vendor', altKey: 'vendor_name' });
    fields.push({ key: 'tax_amount', label: 'Tax' });
    fields.push({ key: 'total_amount', label: 'Total' });
    fields.push({ key: 'notes', label: 'Notes' });
  } else if (type === 'invoice') {
    fields.push({ key: 'number', label: 'Number', altKey: 'invoice_number' });
    fields.push({ key: 'date', label: 'Date', altKey: 'invoice_date', formatter: safeFormatDate });
    fields.push({ key: 'due_date', label: 'Due Date', formatter: safeFormatDate });
    fields.push({ key: 'total_amount', label: 'Total' });
    fields.push({ key: 'currency', label: 'Currency' });
    fields.push({ key: 'client_name', label: 'Client' });
    fields.push({ key: 'vendor_name', label: 'Vendor' });
  } else if (type === 'statement') {
    fields.push({ key: 'transaction_count', label: 'Transaction Count' });
  }

  // Handle detailed transaction differences for statements
  const transactionDiffs = [];
  if (type === 'statement' && reviewResult.transactions) {
    const origTxs = originalData.transactions || [];
    const revTxs = reviewResult.transactions || [];
    const maxIdx = Math.max(origTxs.length, revTxs.length);

    for (let i = 0; i < maxIdx; i++) {
        const t1 = origTxs[i];
        const t2 = revTxs[i];

        // Simple heuristic for diff
        if (!t1 || !t2 || safeFormatDate(t1.date) !== safeFormatDate(t2.date) || t1.amount !== t2.amount || t1.description !== t2.description) {
            transactionDiffs.push({
                index: i + 1,
                original: t1,
                reviewed: t2
            });
        }
    }
  }

  const hasDifferences = fields.some(f => {
    const v1 = originalData[f.key];
    const v2 = reviewResult[f.key];
    // Simple equality check, can be improved
    return JSON.stringify(v1) !== JSON.stringify(v2);
  });

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Review Differences
          </DialogTitle>
          <DialogDescription>
            Review the differences found by the secondary AI reviewer. Accept to apply these changes.
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-[120px_1fr_24px_1fr] gap-4 py-2 font-semibold text-sm border-b-2 border-primary/20 bg-muted/20 px-4 -mx-4 mt-4">
          <div>Field</div>
          <div>Current Value</div>
          <div></div>
          <div>Reviewer Value</div>
        </div>

        <ScrollArea className="flex-1 -mx-4 px-4">
            {fields.map(field => (
              <DiffRow
                key={field.key}
                label={field.label}
                originalValue={originalData[field.key]}
                newValue={reviewResult[field.key] !== undefined ? reviewResult[field.key] : reviewResult[field.altKey]}
                formatter={field.formatter}
              />
            ))}

            {transactionDiffs.length > 0 && (
              <div className="mt-8 space-y-4">
                <h3 className="font-bold text-sm flex items-center gap-2 text-amber-600">
                  <AlertTriangle className="h-4 w-4" />
                  Transaction Differences ({transactionDiffs.length})
                </h3>
                <div className="space-y-4">
                  {transactionDiffs.map((diff) => (
                    <div key={diff.index} className="border rounded-md p-3 bg-amber-500/5 border-amber-500/10">
                      <div className="font-semibold text-xs mb-2 text-muted-foreground uppercase flex justify-between">
                        <span>Transaction #{diff.index}</span>
                        {!diff.original && <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">New</Badge>}
                        {!diff.reviewed && <Badge variant="outline" className="bg-red-500/10 text-red-600 border-red-500/20">Removed</Badge>}
                      </div>

                      <div className="space-y-1">
                         <div className="grid grid-cols-[80px_1fr_20px_1fr] gap-2 text-xs items-center">
                            <span className="text-muted-foreground">Date</span>
                            <span className={cn(safeFormatDate(diff.original?.date) !== safeFormatDate(diff.reviewed?.date) ? "line-through text-muted-foreground" : "")}>
                              {safeFormatDate(diff.original?.date) || 'N/A'}
                            </span>
                            <ArrowRight className="h-3 w-3 text-muted-foreground" />
                            <span className="font-medium text-amber-600">
                              {safeFormatDate(diff.reviewed?.date) || 'N/A'}
                            </span>
                         </div>
                         <div className="grid grid-cols-[80px_1fr_20px_1fr] gap-2 text-xs items-center">
                            <span className="text-muted-foreground">Amount</span>
                            <span className={cn(diff.original?.amount !== diff.reviewed?.amount ? "line-through text-muted-foreground" : "")}>
                              {diff.original?.amount ?? 'N/A'}
                            </span>
                            <ArrowRight className="h-3 w-3 text-muted-foreground" />
                            <span className="font-medium text-amber-600">
                              {diff.reviewed?.amount ?? 'N/A'}
                            </span>
                         </div>
                         <div className="grid grid-cols-[80px_1fr_20px_1fr] gap-2 text-xs items-start">
                            <span className="text-muted-foreground pt-0.5">Description</span>
                            <span className={cn("line-clamp-2", diff.original?.description !== diff.reviewed?.description ? "line-through text-muted-foreground" : "")}>
                              {diff.original?.description || 'N/A'}
                            </span>
                            <ArrowRight className="h-3 w-3 text-muted-foreground pt-0.5" />
                            <span className="font-medium text-amber-600 line-clamp-2">
                              {diff.reviewed?.description || 'N/A'}
                            </span>
                         </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
        </ScrollArea>

        <DialogFooter className="mt-6 gap-2 sm:justify-between">
            <Button variant="secondary" onClick={onRetrigger} disabled={isRetriggering}>
              {isRetriggering ? 'Starting...' : 'Retrigger Review'}
            </Button>

            <div className="flex gap-2">
              <Button variant="outline" onClick={onReject} disabled={isRejecting}>
                {isRejecting ? 'Dismissing...' : (
                  <>
                    <X className="w-4 h-4 mr-2" />
                    Dismiss
                  </>
                )}
              </Button>
              <Button onClick={onAccept} disabled={isAccepting} className="bg-amber-600 hover:bg-amber-700 text-white">
                {isAccepting ? (
                  <span className="flex items-center gap-2">Processing...</span>
                ) : (
                  <>
                    <Check className="w-4 h-4 mr-2" />
                    Accept Review
                  </>
                )}
              </Button>
           </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
