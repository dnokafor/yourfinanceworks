import React, { useState } from 'react';
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
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { Wallet, Tag, Layers, Database, Calendar, DollarSign, Plus } from 'lucide-react';

interface CreateHoldingDialogProps {
  portfolioId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const SECURITY_TYPES = [
  { value: 'stock', label: 'Stock' },
  { value: 'bond', label: 'Bond' },
  { value: 'mutual_fund', label: 'Mutual Fund' },
  { value: 'etf', label: 'ETF' },
  { value: 'cash', label: 'Cash' },
];

const ASSET_CLASSES = [
  { value: 'stocks', label: 'Stocks' },
  { value: 'bonds', label: 'Bonds' },
  { value: 'cash', label: 'Cash' },
  { value: 'real_estate', label: 'Real Estate' },
  { value: 'commodities', label: 'Commodities' },
];

const CreateHoldingDialog: React.FC<CreateHoldingDialogProps> = ({
  portfolioId,
  open,
  onOpenChange,
}) => {
  const queryClient = useQueryClient();
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    security_symbol: '',
    security_name: '',
    security_type: 'stock',
    asset_class: 'stocks',
    quantity: '',
    cost_basis: '',
    purchase_date: new Date().toISOString().split('T')[0],
  });

  const createHoldingMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const payload = {
        ...data,
        quantity: parseFloat(data.quantity),
        cost_basis: parseFloat(data.cost_basis),
      };
      const response = await api.post(
        `/investments/portfolios/${portfolioId}/holdings`,
        payload
      );
      return response;
    },
    onSuccess: () => {
      toast.success(t('Holding added successfully'));
      queryClient.invalidateQueries({ queryKey: ['holdings', portfolioId] });
      queryClient.invalidateQueries({ queryKey: ['portfolio', portfolioId] });
      onOpenChange(false);
      setFormData({
        security_symbol: '',
        security_name: '',
        security_type: 'stock',
        asset_class: 'stocks',
        quantity: '',
        cost_basis: '',
        purchase_date: new Date().toISOString().split('T')[0],
      });
    },
    onError: (error: any) => {
      const errorMessage = error?.response?.data?.detail || t('Failed to add holding');
      toast.error(errorMessage);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.security_symbol.trim()) {
      toast.error(t('Security symbol is required'));
      return;
    }
    if (!formData.quantity || parseFloat(formData.quantity) <= 0) {
      toast.error(t('Quantity must be greater than 0'));
      return;
    }
    if (!formData.cost_basis || parseFloat(formData.cost_basis) <= 0) {
      toast.error(t('Cost basis must be greater than 0'));
      return;
    }

    createHoldingMutation.mutate(formData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] rounded-3xl p-0 overflow-hidden border-border/40 shadow-2xl">
        <DialogHeader className="p-8 bg-primary/5 border-b border-primary/10">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-primary text-white shadow-lg">
              <Plus className="w-6 h-6" />
            </div>
            <div>
              <DialogTitle className="text-2xl font-bold tracking-tight">{t('Add New Position')}</DialogTitle>
              <DialogDescription className="text-muted-foreground pt-1">
                {t('Record a new investment or holding in this portfolio.')}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="p-8 space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Symbol & Name */}
            <div className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="symbol" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/70 ml-1 flex items-center gap-2">
                  <Tag className="w-3 h-3" /> {t('Security Symbol')} *
                </Label>
                <Input
                  id="symbol"
                  placeholder="e.g., AAPL"
                  value={formData.security_symbol}
                  onChange={(e) =>
                    setFormData({ ...formData, security_symbol: e.target.value.toUpperCase() })
                  }
                  className="h-12 rounded-xl border-border/50 focus:ring-primary/20 font-black"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="name" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/70 ml-1 flex items-center gap-2">
                  <Wallet className="w-3 h-3" /> {t('Security Name')}
                </Label>
                <Input
                  id="name"
                  placeholder="e.g., Apple Inc."
                  value={formData.security_name}
                  onChange={(e) => setFormData({ ...formData, security_name: e.target.value })}
                  className="h-12 rounded-xl border-border/50 focus:ring-primary/20 font-medium"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="purchase-date" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/70 ml-1 flex items-center gap-2">
                  <Calendar className="w-3 h-3" /> {t('Purchase Date')} *
                </Label>
                <Input
                  id="purchase-date"
                  type="date"
                  value={formData.purchase_date}
                  onChange={(e) => setFormData({ ...formData, purchase_date: e.target.value })}
                  className="h-12 rounded-xl border-border/50 focus:ring-primary/20 font-medium"
                  required
                />
              </div>
            </div>

            {/* Classification & Numbers */}
            <div className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="type" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/70 ml-1 flex items-center gap-2">
                  <Layers className="w-3 h-3" /> {t('Security Type')} *
                </Label>
                <Select
                  value={formData.security_type}
                  onValueChange={(value) =>
                    setFormData({ ...formData, security_type: value })
                  }
                >
                  <SelectTrigger className="h-12 rounded-xl border-border/50">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="rounded-xl border-border/50 shadow-2xl">
                    {SECURITY_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value} className="rounded-lg m-1">
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="asset-class" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/70 ml-1 flex items-center gap-2">
                  <Database className="w-3 h-3" /> {t('Asset Class')} *
                </Label>
                <Select
                  value={formData.asset_class}
                  onValueChange={(value) =>
                    setFormData({ ...formData, asset_class: value })
                  }
                >
                  <SelectTrigger className="h-12 rounded-xl border-border/50">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="rounded-xl border-border/50 shadow-2xl">
                    {ASSET_CLASSES.map((assetClass) => (
                      <SelectItem key={assetClass.value} value={assetClass.value} className="rounded-lg m-1">
                        {assetClass.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="quantity" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/70 ml-1">
                    {t('Quantity')} *
                  </Label>
                  <Input
                    id="quantity"
                    type="number"
                    step="0.0001"
                    placeholder="0.00"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    className="h-12 rounded-xl border-border/50 focus:ring-primary/20 font-mono"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cost-basis" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/70 ml-1 flex items-center gap-1">
                     {t('Total Cost')} *
                  </Label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground font-bold text-sm">$</span>
                    <Input
                      id="cost-basis"
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      value={formData.cost_basis}
                      onChange={(e) => setFormData({ ...formData, cost_basis: e.target.value })}
                      className="h-12 pl-7 rounded-xl border-border/50 focus:ring-primary/20 font-mono"
                      required
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter className="pt-8 border-t border-border/30 gap-3 sm:gap-0">
            <ProfessionalButton
              type="button"
              variant="outline"
              className="rounded-xl px-8 h-12 flex-1"
              onClick={() => onOpenChange(false)}
            >
              {t('Cancel')}
            </ProfessionalButton>
            <ProfessionalButton
              type="submit"
              variant="gradient"
              className="rounded-xl px-10 h-12 flex-1 shadow-lg shadow-primary/20"
              loading={createHoldingMutation.isPending}
            >
              {t('Add Position')}
            </ProfessionalButton>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateHoldingDialog;
