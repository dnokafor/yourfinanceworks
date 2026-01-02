import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from "react-i18next";
import {
  ProfessionalCard,
  ProfessionalCardContent,
  ProfessionalCardHeader,
  ProfessionalCardTitle,
  ProfessionalCardFooter
} from '@/components/ui/professional-card';
import { ProfessionalButton } from '@/components/ui/professional-button';
import { ProfessionalInput } from '@/components/ui/professional-input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Loader2, CheckCircle2, XCircle, AlertTriangle, Key, Calendar, Shield, ExternalLink, Activity, Info, Lock, User, List, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import { useFeatures } from '@/contexts/FeatureContext';
import { cn } from '@/lib/utils';

interface LicenseInfo {
  installation_id: string;
  license_status: string;
  usage_type: string;
  usage_type_selected: boolean;
  is_licensed: boolean;
  is_personal: boolean;
  is_trial: boolean;
  license_type: string | null;
  trial_info: {
    is_trial: boolean;
    trial_active: boolean;
    trial_start_date: string | null;
    trial_end_date: string | null;
    days_remaining: number;
    in_grace_period: boolean;
    grace_period_end: string | null;
  };
  license_info: {
    activated_at: string | null;
    expires_at: string | null;
    customer_email: string | null;
    customer_name: string | null;
    organization_name: string | null;
  };
  enabled_features: string[];
  has_all_features: boolean;
}

interface FeatureInfo {
  id: string;
  name: string;
  description: string;
  category: string;
  enabled: boolean;
}

export const LicenseManagementTab: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [showDeactivateDialog, setShowDeactivateDialog] = useState(false);
  const [licenseKey, setLicenseKey] = useState('');
  const { refetch: refetchFeaturesContext } = useFeatures();

  // Queries
  const { data: licenseStatus = null, isLoading: loadingStatus } = useQuery<LicenseInfo>({
    queryKey: ['license-status'],
    queryFn: () => api.get<LicenseInfo>('/license/status'),
  });

  const { data: featuresData = { features: [] }, isLoading: loadingFeatures } = useQuery<{ features: FeatureInfo[] }>({
    queryKey: ['license-features'],
    queryFn: () => api.get<{ features: FeatureInfo[] }>('/license/features'),
  });

  const features = (featuresData.features || [])
    .filter(feature => !feature.id.includes('tax') && !feature.name.toLowerCase().includes('tax service integration'))
    .map(feature => {
      const enabledFeatureIds = licenseStatus?.enabled_features || [];
      const hasAllFeatures = licenseStatus?.has_all_features || enabledFeatureIds.includes('all');
      return {
        ...feature,
        enabled: hasAllFeatures || enabledFeatureIds.includes(feature.id)
      };
    });

  // Mutations
  const activateMutation = useMutation({
    mutationFn: (key: string) => api.post<{ success: boolean; message: string }>('/license/activate', { license_key: key }),
    onSuccess: (response) => {
      if (response.success) {
        toast.success(t('license.activate.success'));
        setLicenseKey('');
        queryClient.invalidateQueries({ queryKey: ['license-status'] });
        queryClient.invalidateQueries({ queryKey: ['license-features'] });
        refetchFeaturesContext();
      } else {
        toast.error(response.message || t('license.activate.error'));
      }
    },
    onError: (error: any) => {
      console.error('Failed to activate license:', error);
      toast.error(error.message || t('license.activate.error'));
    }
  });

  const deactivateMutation = useMutation({
    mutationFn: () => api.post<{ success: boolean; message: string }>('/license/deactivate'),
    onSuccess: (response) => {
      if (response.success) {
        toast.success(t('license.status.deactivateSuccess'));
        queryClient.invalidateQueries({ queryKey: ['license-status'] });
        queryClient.invalidateQueries({ queryKey: ['license-features'] });
        refetchFeaturesContext();
        setShowDeactivateDialog(false);
      } else {
        toast.error(response.message || t('license.status.deactivateError'));
      }
    },
    onError: (error: any) => {
      console.error('Failed to deactivate license:', error);
      toast.error(error.message || t('license.status.deactivateError'));
    }
  });

  const handleActivateLicense = () => {
    if (!licenseKey.trim()) {
      toast.error(t('license.activate.enterKey'));
      return;
    }
    activateMutation.mutate(licenseKey.trim());
  };

  const handleDeactivateLicense = () => {
    setShowDeactivateDialog(true);
  };

  const confirmDeactivateLicense = () => {
    deactivateMutation.mutate();
  };

  const loading = loadingStatus || loadingFeatures;
  const activating = activateMutation.isPending;
  const deactivating = deactivateMutation.isPending;
  const licenseInfo = licenseStatus;

  const getLicenseStatusBadge = () => {
    if (!licenseInfo) return null;

    if (licenseInfo.is_licensed) {
      if (licenseInfo.trial_info.in_grace_period) {
        return <Badge variant="destructive" className="ml-2 shadow-sm">{t('license.badges.expiredGrace')}</Badge>;
      }
      const daysRemaining = getLicenseDaysRemaining();
      if (daysRemaining <= 0) {
        return <Badge variant="destructive" className="ml-2 shadow-sm">{t('license.badges.expired')}</Badge>;
      }
      if (daysRemaining <= 30) {
        return <Badge variant="outline" className="ml-2 border-amber-500 text-amber-700 bg-amber-50 shadow-sm">{t('license.badges.expiringSoon')}</Badge>;
      }
      return <Badge variant="default" className="ml-2 bg-green-600 hover:bg-green-700 shadow-sm">{t('license.badges.active')}</Badge>;
    }

    if (licenseInfo.trial_info.trial_active) {
      const daysRemaining = licenseInfo.trial_info.days_remaining;
      if (daysRemaining <= 0) {
        return <Badge variant="destructive" className="ml-2 shadow-sm">{t('license.badges.trialExpired')}</Badge>;
      }
      if (daysRemaining <= 7) {
        return <Badge variant="outline" className="ml-2 border-amber-500 text-amber-700 bg-amber-50 shadow-sm">{t('license.badges.trialEndingSoon')}</Badge>;
      }
      return <Badge variant="secondary" className="ml-2 bg-indigo-100 text-indigo-800 hover:bg-indigo-200 shadow-sm">{t('license.badges.trialActive')}</Badge>;
    }

    if (licenseInfo.is_personal) {
      return <Badge variant="default" className="ml-2 bg-blue-600 hover:bg-blue-700 shadow-sm">{t('license.badges.personalUse')}</Badge>;
    }

    return <Badge variant="outline" className="ml-2 bg-muted/50">{t('license.badges.noLicense')}</Badge>;
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getLicenseDaysRemaining = (): number => {
    if (!licenseInfo?.is_licensed || !licenseInfo.license_info?.expires_at) {
      return 0;
    }
    const expiresAt = new Date(licenseInfo.license_info.expires_at);
    const now = new Date();
    const daysRemaining = Math.ceil((expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return Math.max(0, daysRemaining);
  };

  const groupFeaturesByCategory = () => {
    const grouped: Record<string, FeatureInfo[]> = {};
    features.forEach(feature => {
      if (!grouped[feature.category]) {
        grouped[feature.category] = [];
      }
      grouped[feature.category].push(feature);
    });
    return grouped;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const groupedFeatures = groupFeaturesByCategory();
  const licenseDaysRemaining = getLicenseDaysRemaining();
  const showWarning = licenseInfo && (
    (licenseInfo.trial_info.trial_active && licenseInfo.trial_info.days_remaining <= 7) ||
    (licenseInfo.is_licensed && licenseDaysRemaining <= 30) ||
    licenseInfo.trial_info.in_grace_period
  );

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Warning Banner */}
      {showWarning && (
        <Alert variant={licenseInfo.trial_info.in_grace_period || (licenseInfo.trial_info.trial_active && licenseInfo.trial_info.days_remaining <= 0) || (licenseInfo.is_licensed && licenseDaysRemaining <= 0) ? 'destructive' : 'default'} className="border-amber-200 bg-amber-50 shadow-md">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertTitle className="text-amber-900 font-semibold">{t('license.warnings.actionRequired')}</AlertTitle>
          <AlertDescription className="text-amber-800">
            {licenseInfo.trial_info.in_grace_period && (
              <p>{t('license.warnings.gracePeriod')}</p>
            )}
            {licenseInfo.trial_info.trial_active && licenseInfo.trial_info.days_remaining <= 0 && (
              <p>{t('license.warnings.trialEnded')}</p>
            )}
            {licenseInfo.trial_info.trial_active && licenseInfo.trial_info.days_remaining > 0 && licenseInfo.trial_info.days_remaining <= 7 && (
              <p>{t('license.warnings.trialEnding', { days: licenseInfo.trial_info.days_remaining })}</p>
            )}
            {licenseInfo.is_licensed && !licenseInfo.trial_info.in_grace_period && licenseDaysRemaining <= 30 && licenseDaysRemaining > 0 && (
              <p>{t('license.warnings.expiring', { days: licenseDaysRemaining })}</p>
            )}
            {licenseInfo.is_licensed && licenseDaysRemaining <= 0 && (
              <p>{t('license.warnings.expired')}</p>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* License Status Card */}
      <ProfessionalCard variant="elevated">
        <ProfessionalCardHeader>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <ProfessionalCardTitle className="flex items-center text-xl">
                <Shield className="h-6 w-6 mr-3 text-primary" />
                {t('license.status.title')}
                <div className="ml-2 transform scale-90 origin-left">
                  {getLicenseStatusBadge()}
                </div>
              </ProfessionalCardTitle>
              <p className="text-muted-foreground mt-1 ml-9">
                {t('license.status.description')}
              </p>
            </div>
            {licenseInfo?.is_licensed && (
              <div className="">
                <AlertDialog open={showDeactivateDialog} onOpenChange={setShowDeactivateDialog}>
                  <AlertDialogTrigger asChild>
                    <ProfessionalButton variant="outline" size="sm" onClick={handleDeactivateLicense}>
                      <Lock className="h-3.5 w-3.5 mr-2 text-muted-foreground" />
                      {t('license.status.deactivate')}
                    </ProfessionalButton>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>{t('license.deactivateDialog.title')}</AlertDialogTitle>
                      <AlertDialogDescription>
                        {t('license.deactivateDialog.description')}
                        <div className="bg-muted p-4 rounded-md my-3 border border-border/50">
                          <ul className="list-disc space-y-1 ml-4 text-sm">
                            <li>{t('license.deactivateDialog.featureList.promptManagement')}</li>
                            <li>{t('license.deactivateDialog.featureList.aiInvoiceProcessing')}</li>
                            <li>{t('license.deactivateDialog.featureList.aiExpenseProcessing')}</li>
                            <li>{t('license.deactivateDialog.featureList.advancedReporting')}</li>
                            <li>{t('license.deactivateDialog.featureList.approvalWorkflows')}</li>
                            <li>{t('license.deactivateDialog.featureList.allPremiumFeatures')}</li>
                          </ul>
                        </div>
                        <p className="font-medium text-foreground">{t('license.deactivateDialog.reactivateNote')}</p>
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>{t('license.deactivateDialog.cancel')}</AlertDialogCancel>
                      <AlertDialogAction onClick={confirmDeactivateLicense} disabled={deactivating} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                        {deactivating ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            {t('license.deactivateDialog.deactivating')}
                          </>
                        ) : (
                          t('license.deactivateDialog.confirmButton')
                        )}
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            )}
          </div>
        </ProfessionalCardHeader>
        <ProfessionalCardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-muted/20 p-6 rounded-xl border border-border/50">
            <div className="space-y-2">
              <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold flex items-center gap-1.5">
                <Key className="h-3.5 w-3.5" />
                {t('license.status.installationId')}
              </Label>
              <div className="flex items-center gap-2">
                <code className="text-sm font-mono bg-background border border-border px-3 py-1.5 rounded-md shadow-sm select-all">
                  {licenseInfo?.installation_id || 'N/A'}
                </code>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold flex items-center gap-1.5">
                <Activity className="h-3.5 w-3.5" />
                {t('license.status.usageType')}
              </Label>
              <div className="text-sm font-medium px-3 py-1.5 bg-background border border-border rounded-md shadow-sm inline-block min-w-[120px]">
                {licenseInfo?.is_personal ? 'Core' :
                  licenseInfo?.license_type === 'trial' ? 'Trial' :
                    licenseInfo?.license_type === 'commercial' ? 'Commercial' :
                      licenseInfo?.is_trial ? 'Trial' :
                        licenseInfo?.is_licensed ? 'Commercial' :
                          'Not Selected'}
              </div>
            </div>

            {licenseInfo?.trial_info.trial_active && (
              <>
                <div className="space-y-2">
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5" />
                    {t('license.status.trialPeriod')}
                  </Label>
                  <div className="text-sm font-medium px-3 py-1.5 bg-background border border-border rounded-md shadow-sm">
                    {formatDate(licenseInfo.trial_info.trial_start_date || undefined)} - {formatDate(licenseInfo.trial_info.trial_end_date || undefined)}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5" />
                    {t('license.status.daysRemaining')}
                  </Label>
                  <div className="text-sm font-bold text-primary px-3 py-1.5 bg-primary/5 border border-primary/10 rounded-md">
                    {licenseInfo.trial_info.days_remaining} {t('license.recurrence.days')}
                  </div>
                </div>
              </>
            )}

            {licenseInfo?.is_licensed && licenseInfo.license_info.expires_at && (
              <>
                <div className="space-y-2">
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5" />
                    {t('license.status.expiration')}
                  </Label>
                  <div className="text-sm font-medium flex items-center gap-2 px-3 py-1.5 bg-background border border-border rounded-md shadow-sm">
                    {formatDate(licenseInfo.license_info.expires_at)}
                  </div>
                </div>
                {licenseInfo.license_info.customer_name && (
                  <div className="space-y-2">
                    <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold flex items-center gap-1.5">
                      <User className="h-3.5 w-3.5" />
                      {t('license.status.licensedTo')}
                    </Label>
                    <div className="text-sm font-medium px-3 py-1.5 bg-background border border-border rounded-md shadow-sm text-ellipsis overflow-hidden whitespace-nowrap">
                      {licenseInfo.license_info.customer_name}
                      {licenseInfo.license_info.organization_name && ` (${licenseInfo.license_info.organization_name})`}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </ProfessionalCardContent>
      </ProfessionalCard>

      {/* License Activation Card */}
      {(!licenseInfo?.is_licensed || licenseInfo.trial_info.in_grace_period || (licenseInfo.is_licensed && licenseInfo.license_info?.expires_at && new Date(licenseInfo.license_info.expires_at) < new Date())) && (
        <ProfessionalCard variant="elevated" className="border-primary/20 shadow-lg shadow-primary/5">
          <ProfessionalCardHeader>
            <ProfessionalCardTitle className="flex items-center text-xl text-primary">
              <Key className="h-6 w-6 mr-3" />
              {t('license.activate.title')}
            </ProfessionalCardTitle>
            <p className="text-muted-foreground mt-1 ml-9">
              {t('license.activate.description')}
            </p>
          </ProfessionalCardHeader>
          <ProfessionalCardContent className="space-y-6">
            <div className="grid gap-4 max-w-xl ml-9">
              <ProfessionalInput
                id="license-key"
                label={t('license.activate.keyLabel')}
                placeholder={t('license.activate.keyPlaceholder')}
                value={licenseKey}
                onChange={(e) => setLicenseKey(e.target.value)}
                disabled={activating}
                className="font-mono"
                leftIcon={<Key className="h-4 w-4 text-muted-foreground" />}
              />

              <div className="flex gap-3 pt-2">
                <ProfessionalButton
                  onClick={handleActivateLicense}
                  disabled={activating || !licenseKey.trim()}
                  loading={activating}
                  className="flex-1 sm:flex-none"
                  variant="gradient"
                >
                  {t('license.activate.button')}
                </ProfessionalButton>
                <ProfessionalButton variant="outline" asChild className="flex-1 sm:flex-none">
                  <a href="https://your-pricing-page.com" target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="mr-2 h-4 w-4" />
                    {t('license.activate.purchase')}
                  </a>
                </ProfessionalButton>
              </div>
            </div>
          </ProfessionalCardContent>
        </ProfessionalCard>
      )}

      {/* Features Card */}
      <ProfessionalCard variant="default">
        <ProfessionalCardHeader>
          <ProfessionalCardTitle className="flex items-center">
            <List className="h-5 w-5 mr-2 text-primary" />
            {t('license.features.title')}
          </ProfessionalCardTitle>
          <p className="text-muted-foreground mt-1 ml-7">
            {t('license.features.description')}
          </p>
        </ProfessionalCardHeader>
        <ProfessionalCardContent>
          <div className="space-y-8">
            {Object.entries(groupedFeatures).map(([category, categoryFeatures]) => (
              <div key={category} className="space-y-4">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2 border-b border-border/50 pb-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary/50" />
                  {category}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {categoryFeatures.map((feature) => (
                    <div
                      key={feature.id}
                      className={cn(
                        "flex items-start gap-3 p-4 rounded-xl border transition-all duration-200",
                        feature.enabled
                          ? "bg-card border-border/50 shadow-sm hover:shadow-md hover:border-primary/20"
                          : "bg-muted/30 border-transparent opacity-80"
                      )}
                    >
                      {feature.enabled ? (
                        <div className="mt-0.5 p-1 bg-green-100 text-green-700 rounded-full">
                          <CheckCircle2 className="h-4 w-4" />
                        </div>
                      ) : (
                        <div className="mt-0.5 p-1 bg-muted text-muted-foreground rounded-full">
                          <XCircle className="h-4 w-4" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className={`text-sm font-semibold ${feature.enabled ? 'text-foreground' : 'text-muted-foreground'}`}>
                            {feature.name}
                          </p>
                          {feature.enabled && (
                            <Badge variant="secondary" className="text-[10px] h-5 bg-primary/5 text-primary border-primary/10">{t('license.features.enabled')}</Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{feature.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </ProfessionalCardContent>
      </ProfessionalCard>

      {/* Help Card */}
      <ProfessionalCard variant="minimal" className="bg-muted/10 border border-border/40">
        <ProfessionalCardContent className="p-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
                <Info className="h-6 w-6" />
              </div>
              <div>
                <h3 className="font-semibold text-base mb-1">{t('license.help.title')}</h3>
                <p className="text-sm text-muted-foreground max-w-lg">
                  {t('license.help.description')}
                </p>
              </div>
            </div>
            <div className="flex gap-3 w-full md:w-auto">
              <ProfessionalButton variant="outline" size="sm" asChild className="flex-1 md:flex-none">
                <a href="mailto:support@example.com">
                  {t('license.help.contactSupport')}
                </a>
              </ProfessionalButton>
              <ProfessionalButton variant="outline" size="sm" asChild className="flex-1 md:flex-none">
                <a href="https://docs.example.com/licensing" target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  {t('license.help.documentation')}
                </a>
              </ProfessionalButton>
            </div>
          </div>
        </ProfessionalCardContent>
      </ProfessionalCard>
    </div>
  );
};
