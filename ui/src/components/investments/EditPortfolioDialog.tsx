import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { ProfessionalButton } from '@/components/ui/professional-button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { investmentApi, InvestmentPortfolio } from '@/lib/api';
import { toast } from 'sonner';

interface EditPortfolioDialogProps {
  portfolio: InvestmentPortfolio;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const EditPortfolioDialog: React.FC<EditPortfolioDialogProps> = ({
  portfolio,
  open,
  onOpenChange,
}) => {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  const [formData, setFormData] = useState({
    name: portfolio.name,
    portfolio_type: portfolio.portfolio_type as 'taxable' | 'retirement' | 'business',
    currency: portfolio.currency || 'USD'
  });

  useEffect(() => {
    if (open) {
      setFormData({
        name: portfolio.name,
        portfolio_type: portfolio.portfolio_type as 'taxable' | 'retirement' | 'business',
        currency: portfolio.currency || 'USD'
      });
    }
  }, [open, portfolio]);

  const updatePortfolioMutation = useMutation({
    mutationFn: (data: typeof formData) => investmentApi.update(portfolio.id, data),
    onSuccess: () => {
      toast.success(t('Portfolio updated successfully'));
      queryClient.invalidateQueries({ queryKey: ['portfolio', portfolio.id] });
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
      onOpenChange(false);
    },
    onError: (error: any) => {
      const errorMessage = error?.response?.data?.detail || t('Failed to update portfolio');
      toast.error(errorMessage);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error(t('Portfolio name is required'));
      return;
    }
    updatePortfolioMutation.mutate(formData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[450px] rounded-3xl p-0 overflow-hidden border-border/40 shadow-2xl">
        <DialogHeader className="p-8 bg-primary/5 border-b border-primary/10">
          <DialogTitle className="text-2xl font-bold tracking-tight">{t('Edit Portfolio')}</DialogTitle>
          <DialogDescription className="text-muted-foreground pt-1">
            {t('Update your portfolio information and base currency.')}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/70 ml-1">
                {t('Portfolio Name')}
              </Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder={t('e.g., Vanguard Retirement')}
                className="h-12 rounded-xl border-border/50 focus:ring-primary/20 font-medium"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="portfolio_type" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/70 ml-1">
                {t('Account Type')}
              </Label>
              <Select
                value={formData.portfolio_type}
                onValueChange={(value: 'taxable' | 'retirement' | 'business') =>
                  setFormData({ ...formData, portfolio_type: value })
                }
              >
                <SelectTrigger className="h-12 rounded-xl border-border/50">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-xl shadow-2xl border-border/50">
                  <SelectItem value="taxable" className="rounded-lg m-1">{t('Taxable Brokerage')}</SelectItem>
                  <SelectItem value="retirement" className="rounded-lg m-1">{t('Retirement (401k, IRA)')}</SelectItem>
                  <SelectItem value="business" className="rounded-lg m-1">{t('Business Investment')}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="currency" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/70 ml-1">
                {t('Base Currency')}
              </Label>
              <Select
                value={formData.currency}
                onValueChange={(value) => setFormData({ ...formData, currency: value })}
              >
                <SelectTrigger className="h-12 rounded-xl border-border/50">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-xl border-border/50 shadow-2xl">
                  <SelectItem value="USD" className="rounded-lg m-1">USD - US Dollar</SelectItem>
                  <SelectItem value="EUR" className="rounded-lg m-1">EUR - Euro</SelectItem>
                  <SelectItem value="GBP" className="rounded-lg m-1">GBP - British Pound</SelectItem>
                  <SelectItem value="CAD" className="rounded-lg m-1">CAD - Canadian Dollar</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter className="pt-4 gap-2 sm:gap-0">
            <ProfessionalButton
              type="button"
              variant="outline"
              className="rounded-xl px-6"
              onClick={() => onOpenChange(false)}
            >
              {t('Cancel')}
            </ProfessionalButton>
            <ProfessionalButton
              type="submit"
              variant="gradient"
              className="rounded-xl px-8 shadow-lg shadow-primary/20"
              loading={updatePortfolioMutation.isPending}
            >
              {t('Save Changes')}
            </ProfessionalButton>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default EditPortfolioDialog;
