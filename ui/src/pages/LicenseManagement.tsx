import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
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
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState(false);
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
      
      const featuresWithStatus = (featuresResponse.features || []).map(feature => ({
        ...feature,
        enabled: hasAllFeatures || enabledFeatureIds.includes(feature.id)
      }));
      
      setFeatures(featuresWithStatus);
    } catch (error) {
      console.error('Failed to fetch license status:', error);
      toast.error('Failed to load license information');
    } finally {
      setLoading(false);
    }
  };

  const handleActivateLicense = async () => {
    if (!licenseKey.trim()) {
      toast.error('Please enter a license key');
      return;
    }

    try {
      setActivating(true);
      const response = await api.post<{ success: boolean; message: string }>('/license/activate', {
        license_key: licenseKey.trim(),
      });

      if (response.success) {
        toast.success('License activated successfully!');
        setLicenseKey('');
        await fetchLicenseStatus();
        await refetch(); // Refresh feature flags
      } else {
        toast.error(response.message || 'Failed to activate license');
      }
    } catch (error: any) {
      console.error('Failed to activate license:', error);
      toast.error(error.message || 'Failed to activate license');
    } finally {
      setActivating(false);
    }
  };

  const handleDeactivateLicense = async () => {
    if (!confirm('Are you sure you want to deactivate your license? This will disable licensed features.')) {
      return;
    }

    try {
      const response = await api.post<{ success: boolean; message: string }>('/license/deactivate');
      
      if (response.success) {
        toast.success('License deactivated successfully');
        await fetchLicenseStatus();
        await refetch(); // Refresh feature flags
      } else {
        toast.error(response.message || 'Failed to deactivate license');
      }
    } catch (error: any) {
      console.error('Failed to deactivate license:', error);
      toast.error(error.message || 'Failed to deactivate license');
    }
  };

  const getLicenseStatusBadge = () => {
    if (!licenseInfo) return null;

    if (licenseInfo.is_licensed) {
      if (licenseInfo.trial_info.in_grace_period) {
        return <Badge variant="destructive" className="ml-2">Expired (Grace Period)</Badge>;
      }
      const daysRemaining = getLicenseDaysRemaining();
      if (daysRemaining <= 0) {
        return <Badge variant="destructive" className="ml-2">Expired</Badge>;
      }
      if (daysRemaining <= 30) {
        return <Badge variant="outline" className="ml-2 border-amber-500 text-amber-700">Expiring Soon</Badge>;
      }
      return <Badge variant="default" className="ml-2 bg-green-600">Active</Badge>;
    }

    if (licenseInfo.trial_info.trial_active) {
      const daysRemaining = licenseInfo.trial_info.days_remaining;
      if (daysRemaining <= 0) {
        return <Badge variant="destructive" className="ml-2">Trial Expired</Badge>;
      }
      if (daysRemaining <= 7) {
        return <Badge variant="outline" className="ml-2 border-amber-500 text-amber-700">Trial Ending Soon</Badge>;
      }
      return <Badge variant="secondary" className="ml-2">Trial Active</Badge>;
    }

    if (licenseInfo.is_personal) {
      return <Badge variant="default" className="ml-2 bg-blue-600">Personal Use</Badge>;
    }

    return <Badge variant="outline" className="ml-2">No License</Badge>;
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
        <span>Loading license information...</span>
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
          <AlertTitle className="text-amber-900">Action Required</AlertTitle>
          <AlertDescription className="text-amber-800">
            {licenseInfo.trial_info.in_grace_period && (
              <p>Your license has expired. You are in a grace period. Please renew your license to continue using all features.</p>
            )}
            {licenseInfo.trial_info.trial_active && licenseInfo.trial_info.days_remaining <= 0 && (
              <p>Your trial period has ended. Activate a license to continue using premium features.</p>
            )}
            {licenseInfo.trial_info.trial_active && licenseInfo.trial_info.days_remaining > 0 && licenseInfo.trial_info.days_remaining <= 7 && (
              <p>Your trial period ends in {licenseInfo.trial_info.days_remaining} days. Activate a license to avoid interruption.</p>
            )}
            {licenseInfo.is_licensed && !licenseInfo.trial_info.in_grace_period && licenseDaysRemaining <= 30 && licenseDaysRemaining > 0 && (
              <p>Your license expires in {licenseDaysRemaining} days. Please renew to avoid service interruption.</p>
            )}
            {licenseInfo.is_licensed && licenseDaysRemaining <= 0 && (
              <p>Your license has expired. Please renew to continue using all features.</p>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* License Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Shield className="h-5 w-5 mr-2" />
            License Status
            {getLicenseStatusBadge()}
          </CardTitle>
          <CardDescription>
            View your current license information and manage your subscription
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">Installation ID</Label>
              <div className="flex items-center gap-2">
                <code className="text-sm bg-muted px-2 py-1 rounded">{licenseInfo?.installation_id || 'N/A'}</code>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">Usage Type</Label>
              <div className="text-sm capitalize">
                {licenseInfo?.usage_type || 'Not Selected'}
              </div>
            </div>

            {licenseInfo?.trial_info.trial_active && (
              <>
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">Trial Period</Label>
                  <div className="text-sm">
                    {formatDate(licenseInfo.trial_info.trial_start_date || undefined)} - {formatDate(licenseInfo.trial_info.trial_end_date || undefined)}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">Days Remaining</Label>
                  <div className="text-sm font-semibold">
                    {licenseInfo.trial_info.days_remaining} days
                  </div>
                </div>
              </>
            )}

            {licenseInfo?.is_licensed && licenseInfo.license_info.expires_at && (
              <>
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">License Expiration</Label>
                  <div className="text-sm flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    {formatDate(licenseInfo.license_info.expires_at)}
                  </div>
                </div>
                {licenseInfo.license_info.customer_name && (
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-muted-foreground">Licensed To</Label>
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
              <Button variant="outline" size="sm" onClick={handleDeactivateLicense}>
                Deactivate License
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* License Activation Card */}
      {(!licenseInfo?.is_licensed || licenseInfo.trial_info.in_grace_period) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Key className="h-5 w-5 mr-2" />
              Activate License
            </CardTitle>
            <CardDescription>
              Enter your license key to activate premium features
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="license-key">License Key</Label>
              <Input
                id="license-key"
                type="text"
                placeholder="Enter your license key"
                value={licenseKey}
                onChange={(e) => setLicenseKey(e.target.value)}
                disabled={activating}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleActivateLicense} disabled={activating || !licenseKey.trim()}>
                {activating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Activate License
              </Button>
              <Button variant="outline" asChild>
                <a href="https://your-pricing-page.com" target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Purchase License
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Features Card */}
      <Card>
        <CardHeader>
          <CardTitle>Available Features</CardTitle>
          <CardDescription>
            Features available in your current plan
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
                            <Badge variant="secondary" className="text-xs">Enabled</Badge>
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
          <CardTitle>Need Help?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground">
            If you have questions about licensing or need assistance, please contact our support team.
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" asChild>
              <a href="mailto:support@example.com">
                Contact Support
              </a>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <a href="https://docs.example.com/licensing" target="_blank" rel="noopener noreferrer">
                <ExternalLink className="mr-2 h-4 w-4" />
                Documentation
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LicenseManagement;
