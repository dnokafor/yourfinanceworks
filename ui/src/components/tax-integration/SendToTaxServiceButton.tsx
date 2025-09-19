import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Loader2, Send } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import { useTranslation } from 'react-i18next';

interface SendToTaxServiceButtonProps {
  itemId: number;
  itemType: 'expense' | 'invoice';
  onSuccess?: () => void;
  disabled?: boolean;
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg';
}

export const SendToTaxServiceButton: React.FC<SendToTaxServiceButtonProps> = ({
  itemId,
  itemType,
  onSuccess,
  disabled = false,
  variant = 'outline',
  size = 'sm',
}) => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);

  const handleSendToTaxService = async () => {
    if (!itemId) {
      toast.error(t('taxIntegration.errors.invalidItemId'));
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.post<{
        success: boolean;
        transaction_id?: string;
        error_message?: string;
      }>(`/tax-integration/send`, {
        item_id: itemId,
        item_type: itemType,
      });

      if (response.success) {
        toast.success(
          t('taxIntegration.success.sentToTaxService', {
            itemType: itemType === 'expense' ? t('common.expense') : t('common.invoice'),
            transactionId: response.transaction_id || 'Unknown',
          })
        );
        onSuccess?.();
      } else {
        toast.error(
          response.error_message || t('taxIntegration.errors.sendFailed')
        );
      }
    } catch (error: any) {
      console.error('Error sending to tax service:', error);
      toast.error(
        error?.message || t('taxIntegration.errors.sendFailed')
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleSendToTaxService}
      disabled={disabled || isLoading}
      className="flex items-center gap-2"
    >
      {isLoading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Send className="h-4 w-4" />
      )}
      {t('taxIntegration.sendToTaxService')}
    </Button>
  );
};
