import React from "react";
import { useTranslation } from "react-i18next";
import { Percent, Plus, Edit, Trash2, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
    ProfessionalCard,
    ProfessionalCardHeader,
    ProfessionalCardTitle,
    ProfessionalCardContent,
} from "@/components/ui/professional-card";
import { ProfessionalButton } from "@/components/ui/professional-button";
import {
    ProfessionalTable,
    ProfessionalTableHeader,
    ProfessionalTableBody,
    ProfessionalTableRow,
    ProfessionalTableCell,
    ProfessionalTableHead,
    StatusBadge,
} from "@/components/ui/professional-table";

export interface DiscountRule {
    id: number;
    name: string;
    min_amount: number;
    discount_type: string;
    discount_value: number;
    is_active: boolean;
    priority: number;
    currency?: string;
}

export interface DiscountRuleCreate {
    name: string;
    min_amount: number;
    discount_type: string;
    discount_value: number;
    is_active: boolean;
    priority: number;
    currency: string;
}

interface DiscountRulesTabProps {
    discountRules: DiscountRule[];
    loading: boolean;
    showDialog: boolean;
    editingRule: DiscountRule | null;
    newRule: DiscountRuleCreate;
    onOpenCreateDialog: () => void;
    onOpenEditDialog: (rule: DiscountRule) => void;
    onCloseDialog: () => void;
    onRuleChange: (field: string, value: any) => void;
    onCreateRule: () => Promise<void>;
    onUpdateRule: () => Promise<void>;
    onDeleteRule: (id: number) => Promise<void>;
}

export const DiscountRulesTab: React.FC<DiscountRulesTabProps> = ({
    discountRules,
    loading,
    showDialog,
    editingRule,
    newRule,
    onOpenCreateDialog,
    onOpenEditDialog,
    onCloseDialog,
    onRuleChange,
    onCreateRule,
    onUpdateRule,
    onDeleteRule,
}) => {
    const { t } = useTranslation();
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = React.useState(false);
    const [ruleToDelete, setRuleToDelete] = React.useState<number | null>(null);

    const handleDeleteClick = (id: number) => {
        setRuleToDelete(id);
        setIsDeleteDialogOpen(true);
    };

    const confirmDelete = async () => {
        if (ruleToDelete !== null) {
            await onDeleteRule(ruleToDelete);
            setIsDeleteDialogOpen(false);
            setRuleToDelete(null);
        }
    };

    return (
        <>
            <ProfessionalCard variant="elevated">
                <ProfessionalCardHeader>
                    <div className="flex items-center justify-between">
                        <ProfessionalCardTitle className="flex items-center gap-2">
                            <Percent className="w-5 h-5 text-primary" />
                            {t('settings.discount_rules.title')}
                        </ProfessionalCardTitle>
                        <ProfessionalButton onClick={onOpenCreateDialog} size="sm" leftIcon={<Plus className="h-4 w-4" />}>
                            {t('settings.discount_rules.create_rule')}
                        </ProfessionalButton>
                    </div>
                </ProfessionalCardHeader>
                <ProfessionalCardContent>
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-primary mr-3" />
                            <span className="text-muted-foreground font-medium">{t('settings.discount_rules.loading')}</span>
                        </div>
                    ) : discountRules.length === 0 ? (
                        <div className="text-center py-12 bg-muted/20 rounded-xl border-2 border-dashed border-border">
                            <Percent className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-20" />
                            <p className="text-muted-foreground font-medium mb-2">{t('settings.discount_rules.no_rules_configured')}</p>
                            <p className="text-sm text-muted-foreground">
                                {t('settings.discount_rules.create_rules_to_apply_discounts')}
                            </p>
                        </div>
                    ) : (
                        <div className="rounded-xl border border-border/50 overflow-hidden">
                            <ProfessionalTable>
                                <ProfessionalTableHeader>
                                    <ProfessionalTableRow>
                                        <ProfessionalTableHead>{t('settings.discount_rules.rule_name')}</ProfessionalTableHead>
                                        <ProfessionalTableHead>{t('settings.discount_rules.discount')}</ProfessionalTableHead>
                                        <ProfessionalTableHead>{t('settings.discount_rules.min_amount')}</ProfessionalTableHead>
                                        <ProfessionalTableHead>{t('settings.discount_rules.priority')}</ProfessionalTableHead>
                                        <ProfessionalTableHead>{t('settings.discount_rules.status')}</ProfessionalTableHead>
                                        <ProfessionalTableHead className="text-right">{t('common.actions')}</ProfessionalTableHead>
                                    </ProfessionalTableRow>
                                </ProfessionalTableHeader>
                                <ProfessionalTableBody>
                                    {discountRules.map((rule) => (
                                        <ProfessionalTableRow key={rule.id} interactive>
                                            <ProfessionalTableCell className="font-medium">
                                                <div className="flex items-center gap-2">
                                                    {rule.name}
                                                    <Badge variant="secondary" className="text-[10px] px-1.5 h-4 uppercase">{rule.currency || "USD"}</Badge>
                                                </div>
                                            </ProfessionalTableCell>
                                            <ProfessionalTableCell>
                                                <span className="font-semibold text-primary">
                                                    {rule.discount_type === "percentage" ? `${rule.discount_value}%` : `$${rule.discount_value}`}
                                                </span>
                                            </ProfessionalTableCell>
                                            <ProfessionalTableCell>${rule.min_amount}</ProfessionalTableCell>
                                            <ProfessionalTableCell>
                                                <Badge variant="outline" className="font-mono">{rule.priority}</Badge>
                                            </ProfessionalTableCell>
                                            <ProfessionalTableCell>
                                                <StatusBadge status={rule.is_active ? 'success' : 'neutral'}>
                                                    {rule.is_active ? t('settings.discount_rules.rule_active') : t('settings.discount_rules.rule_inactive')}
                                                </StatusBadge>
                                            </ProfessionalTableCell>
                                            <ProfessionalTableCell className="text-right">
                                                <div className="flex justify-end gap-2">
                                                    <ProfessionalButton
                                                        variant="ghost"
                                                        size="icon-sm"
                                                        onClick={() => onOpenEditDialog(rule)}
                                                    >
                                                        <Edit className="h-4 w-4" />
                                                    </ProfessionalButton>
                                                    <ProfessionalButton
                                                        variant="ghost"
                                                        size="icon-sm"
                                                        className="text-destructive hover:bg-destructive/10"
                                                        onClick={() => handleDeleteClick(rule.id)}
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </ProfessionalButton>
                                                </div>
                                            </ProfessionalTableCell>
                                        </ProfessionalTableRow>
                                    ))}
                                </ProfessionalTableBody>
                            </ProfessionalTable>
                        </div>
                    )}
                </ProfessionalCardContent>
            </ProfessionalCard>

            {/* Discount Rule Dialog */}
            <Dialog open={showDialog} onOpenChange={onCloseDialog}>
                <DialogContent className="sm:max-w-[500px]">
                    <DialogHeader>
                        <DialogTitle>
                            {editingRule ? t('settings.discount_rules.edit_discount_rule') : t('settings.discount_rules.create_discount_rule')}
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="rule_name">{t('settings.discount_rules.rule_name')}</Label>
                            <Input
                                id="rule_name"
                                value={newRule.name}
                                onChange={(e) => onRuleChange('name', e.target.value)}
                                placeholder={t('settings.discount_rules.rule_name_placeholder')}
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="discount_type">{t('settings.discount_rules.discount_type')}</Label>
                                <Select value={newRule.discount_type} onValueChange={(value) => onRuleChange('discount_type', value)}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="percentage">{t('settings.discount_rules.percentage')}</SelectItem>
                                        <SelectItem value="fixed">{t('settings.discount_rules.fixed_amount')}</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="discount_value">{t('settings.discount_rules.discount_value')}</Label>
                                <Input
                                    id="discount_value"
                                    type="number"
                                    step="0.01"
                                    value={newRule.discount_value}
                                    onChange={(e) => onRuleChange('discount_value', parseFloat(e.target.value))}
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="min_amount">{t('settings.discount_rules.min_amount')}</Label>
                                <Input
                                    id="min_amount"
                                    type="number"
                                    step="0.01"
                                    value={newRule.min_amount}
                                    onChange={(e) => onRuleChange('min_amount', parseFloat(e.target.value))}
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="priority">{t('settings.discount_rules.priority')}</Label>
                                <Input
                                    id="priority"
                                    type="number"
                                    value={newRule.priority}
                                    onChange={(e) => onRuleChange('priority', parseInt(e.target.value))}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="currency">{t('settings.discount_rules.currency')}</Label>
                            <Input
                                id="currency"
                                value={newRule.currency}
                                onChange={(e) => onRuleChange('currency', e.target.value)}
                                placeholder="USD"
                            />
                        </div>

                        <div className="flex items-center space-x-2">
                            <Switch
                                id="is_active"
                                checked={newRule.is_active}
                                onCheckedChange={(checked) => onRuleChange('is_active', checked)}
                            />
                            <Label htmlFor="is_active">{t('settings.active')}</Label>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={onCloseDialog}>
                            {t('settings.cancel')}
                        </Button>
                        <Button onClick={editingRule ? onUpdateRule : onCreateRule}>
                            {editingRule ? t('settings.discount_rules.update_rule') : t('settings.discount_rules.create_rule')}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>{t('settings.discount_rules.delete_confirm_title')}</AlertDialogTitle>
                        <AlertDialogDescription>
                            {t('settings.discount_rules.delete_confirm_description')}
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>{t('common.cancel')}</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={confirmDelete}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                            {t('common.delete')}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
};
