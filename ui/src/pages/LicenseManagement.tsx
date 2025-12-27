import React, { useState, useEffect } from 'react';
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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
import { Loader2, CheckCircle, XCircle, AlertTriangle, Key, Calendar, Shield, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import { useFeatures } from '@/contexts/FeatureContext';

interface LicenseInfo {
  installation_id: string;
  license_status: string;
  usage_type: string;
  usage_type_selected: boolean;
  is_licensed: boolean;
  is_personal: boolean;
  is_trial: boolean;
  license_type: string | null;  // Add license_type from JWT payload
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

export const LicenseManagement: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState(false);
  const [deactivating, setDeactivating] = useState(false);
  const [showDeactivateDialog, setShowDeactivateDialog] = useState(false);
  const [licenseInfo, setLicenseInfo] = useState<LicenseInfo | null>(null);
  const [features, setFeatures] = useState<FeatureInfo[]>([]);
  const [licenseKey, setLicenseKey] = useState('');
  const { refetch } = useFeatures();

  useEffect(() => {
    fetchLicenseStatus();
  }, []);

  const fetchLicenseStatus = async () => {
    try {
      setLoading(true);
      const [statusResponse, featuresResponse] = await Promise.all([
        api.get<LicenseInfo>('/license/status'),
        api.get<{ features: FeatureInfo[] }>('/license/features'),
      ]);

      setLicenseInfo(statusResponse);

      // Map features with actual enabled status from license
      const enabledFeatureIds = statusResponse.enabled_features || [];
      const hasAllFeatures = statusResponse.has_all_features || enabledFeatureIds.includes('all');

      const featuresWithStatus = (featuresResponse.features || [])
        .filter(feature => !feature.id.includes('tax') && !feature.name.toLowerCase().includes('tax service integration'))
        .map(feature => ({
          ...feature,
          enabled: hasAllFeatures || enabledFeatureIds.includes(feature.id)
        }));

      setFeatures(featuresWithStatus);
    } catch (error) {
      console.error('Failed to fetch license status:', error);
      toast.error(t('license.failedToLoad'));
    } finally {
      setLoading(false);
    }
  };

  const handleActivateLicense = async () => {
    if (!licenseKey.trim()) {
      toast.error(t('license.activate.enterKey'));
      return;
    }

    try {
      setActivating(true);
      const response = await api.post<{ success: boolean; message: string }>('/license/activate', {
        license_key: licenseKey.trim(),
      });

      if (response.success) {
        toast.success(t('license.activate.success'));
        setLicenseKey('');
        await fetchLicenseStatus();
        await refetch(); // Refresh feature flags
      } else {
        toast.error(response.message || t('license.activate.error'));
      }
    } catch (error: any) {
      console.error('Failed to activate license:', error);
      toast.error(error.message || t('license.activate.error'));
    } finally {
      setActivating(false);
    }
  };

  const handleDeactivateLicense = async () => {
    setShowDeactivateDialog(true);
  };

  const confirmDeactivateLicense = async () => {
    try {
      setDeactivating(true);
      const response = await api.post<{ success: boolean; message: string }>('/license/deactivate');

      if (response.success) {
        toast.success(t('license.status.deactivateSuccess'));
        await fetchLicenseStatus();
        await refetch(); // Refresh feature flags
        setShowDeactivateDialog(false);
      } else {
        toast.error(response.message || t('license.status.deactivateError'));
      }
    } catch (error: any) {
      console.error('Failed to deactivate license:', error);
      toast.error(error.message || t('license.status.deactivateError'));
    } finally {
      setDeactivating(false);
    }
  };

  const getLicenseStatusBadge = () => {
    if (!licenseInfo) return null;

    if (licenseInfo.is_licensed) {
      if (licenseInfo.trial_info.in_grace_period) {
        return <Badge variant="destructive" className="ml-2">{t('license.badges.expiredGrace')}</Badge>;
      }
      const daysRemaining = getLicenseDaysRemaining();
      if (daysRemaining <= 0) {
        return <Badge variant="destructive" className="ml-2">{t('license.badges.expired')}</Badge>;
      }
      if (daysRemaining <= 30) {
        return <Badge variant="outline" className="ml-2 border-amber-500 text-amber-700">{t('license.badges.expiringSoon')}</Badge>;
      }
      return <Badge variant="default" className="ml-2 bg-green-600">{t('license.badges.active')}</Badge>;
    }

    if (licenseInfo.trial_info.trial_active) {
      const daysRemaining = licenseInfo.trial_info.days_remaining;
      if (daysRemaining <= 0) {
        return <Badge variant="destructive" className="ml-2">{t('license.badges.trialExpired')}</Badge>;
      }
      if (daysRemaining <= 7) {
        return <Badge variant="outline" className="ml-2 border-amber-500 text-amber-700">{t('license.badges.trialEndingSoon')}</Badge>;
      }
      return <Badge variant="secondary" className="ml-2">{t('license.badges.trialActive')}</Badge>;
    }

    if (licenseInfo.is_personal) {
      return <Badge variant="default" className="ml-2 bg-blue-600">{t('license.badges.personalUse')}</Badge>;
    }

    return <Badge variant="outline" className="ml-2">{t('license.badges.noLicense')}</Badge>;
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
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin mr-2" />
        <span>{t('license.loading')}</span>
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
    <div className="space-y-6">
      {/* Warning Banner */}
      {showWarning && (
        <Alert variant={licenseInfo.trial_info.in_grace_period || (licenseInfo.trial_info.trial_active && licenseInfo.trial_info.days_remaining <= 0) || (licenseInfo.is_licensed && licenseDaysRemaining <= 0) ? 'destructive' : 'default'} className="border-amber-200 bg-amber-50">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertTitle className="text-amber-900">{t('license.warnings.actionRequired')}</AlertTitle>
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
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Shield className="h-5 w-5 mr-2" />
            {t('license.status.title')}
            {getLicenseStatusBadge()}
          </CardTitle>
          <CardDescription>
            {t('license.status.description')}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">{t('license.status.installationId')}</Label>
              <div className="flex items-center gap-2">
                <code className="text-sm bg-muted px-2 py-1 rounded">{licenseInfo?.installation_id || 'N/A'}</code>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">{t('license.status.usageType')}</Label>
              <div className="text-sm capitalize">
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
                  <Label className="text-sm font-medium text-muted-foreground">{t('license.status.trialPeriod')}</Label>
                  <div className="text-sm">
                    {formatDate(licenseInfo.trial_info.trial_start_date || undefined)} - {formatDate(licenseInfo.trial_info.trial_end_date || undefined)}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">{t('license.status.daysRemaining')}</Label>
                  <div className="text-sm font-semibold">
                    {licenseInfo.trial_info.days_remaining} {t('license.recurrence.days')}
                  </div>
                </div>
              </>
            )}

            {licenseInfo?.is_licensed && licenseInfo.license_info.expires_at && (
              <>
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">{t('license.status.expiration')}</Label>
                  <div className="text-sm flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    {formatDate(licenseInfo.license_info.expires_at)}
                  </div>
                </div>
                {licenseInfo.license_info.customer_name && (
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-muted-foreground">{t('license.status.licensedTo')}</Label>
                    <div className="text-sm">
                      {licenseInfo.license_info.customer_name}
                      {licenseInfo.license_info.organization_name && ` (${licenseInfo.license_info.organization_name})`}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {licenseInfo?.is_licensed && (
            <div className="pt-4 border-t">
              <AlertDialog open={showDeactivateDialog} onOpenChange={setShowDeactivateDialog}>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" size="sm" onClick={handleDeactivateLicense}>
                    {t('license.status.deactivate')}
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>{t('license.deactivateDialog.title')}</AlertDialogTitle>
                    <AlertDialogDescription>
                      {t('license.deactivateDialog.description')}
                      <ul className="mt-2 ml-4 list-disc space-y-1">
                        <li>{t('license.deactivateDialog.featureList.promptManagement')}</li>
                        <li>{t('license.deactivateDialog.featureList.aiInvoiceProcessing')}</li>
                        <li>{t('license.deactivateDialog.featureList.aiExpenseProcessing')}</li>
                        <li>{t('license.deactivateDialog.featureList.advancedReporting')}</li>
                        <li>{t('license.deactivateDialog.featureList.approvalWorkflows')}</li>
                        <li>{t('license.deactivateDialog.featureList.allPremiumFeatures')}</li>
                      </ul>
                      {t('license.deactivateDialog.reactivateNote')}
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>{t('license.deactivateDialog.cancel')}</AlertDialogCancel>
                    <AlertDialogAction onClick={confirmDeactivateLicense} disabled={deactivating}>
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
        </CardContent>
      </Card>

      {/* License Activation Card */}
      {(!licenseInfo?.is_licensed || licenseInfo.trial_info.in_grace_period || (licenseInfo.is_licensed && licenseInfo.license_info?.expires_at && new Date(licenseInfo.license_info.expires_at) < new Date())) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Key className="h-5 w-5 mr-2" />
              {t('license.activate.title')}
            </CardTitle>
            <CardDescription>
              {t('license.activate.description')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="license-key">{t('license.activate.keyLabel')}</Label>
              <Input
                id="license-key"
                type="text"
                placeholder={t('license.activate.keyPlaceholder')}
                value={licenseKey}
                onChange={(e) => setLicenseKey(e.target.value)}
                disabled={activating}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleActivateLicense} disabled={activating || !licenseKey.trim()}>
                {activating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {t('license.activate.button')}
              </Button>
              <Button variant="outline" asChild>
                <a href="https://your-pricing-page.com" target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  {t('license.activate.purchase')}
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Features Card */}
      <Card>
        <CardHeader>
          <CardTitle>{t('license.features.title')}</CardTitle>
          <CardDescription>
            {t('license.features.description')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {Object.entries(groupedFeatures).map(([category, categoryFeatures]) => (
              <div key={category} className="space-y-3">
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                  {category}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {categoryFeatures.map((feature) => (
                    <div
                      key={feature.id}
                      className="flex items-start gap-3 p-3 rounded-lg border bg-card"
                    >
                      {feature.enabled ? (
                        <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                      ) : (
                        <XCircle className="h-5 w-5 text-gray-400 flex-shrink-0 mt-0.5" />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium">{feature.name}</p>
                          {feature.enabled && (
                            <Badge variant="secondary" className="text-xs">{t('license.features.enabled')}</Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">{feature.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Help Card */}
      <Card>
        <CardHeader>
          <CardTitle>{t('license.help.title')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground">
            {t('license.help.description')}
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" asChild>
              <a href="mailto:support@example.com">
                {t('license.help.contactSupport')}
              </a>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <a href="https://docs.example.com/licensing" target="_blank" rel="noopener noreferrer">
                <ExternalLink className="mr-2 h-4 w-4" />
                {t('license.help.documentation')}
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LicenseManagement;
