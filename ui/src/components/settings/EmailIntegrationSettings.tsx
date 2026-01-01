import React, { useState, useEffect } from 'react';
import { useTranslation } from "react-i18next";
import {
    ProfessionalCard,
    ProfessionalCardContent,
    ProfessionalCardHeader,
    ProfessionalCardTitle
} from "@/components/ui/professional-card";
import { ProfessionalInput } from "@/components/ui/professional-input";
import { ProfessionalButton } from "@/components/ui/professional-button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
    Mail,
    Save,
    RefreshCw,
    CheckCircle2,
    AlertCircle,
    Loader2,
    Globe,
    User,
    Key,
    Hash,
    List,
    Clock,
    Server
} from "lucide-react";
import { toast } from "sonner";
import { api, getErrorMessage } from "@/lib/api";
import { FeatureGate } from "@/components/FeatureGate";

interface EmailConfig {
    imap_host: string;
    imap_port: number;
    username: string;
    password?: string;
    enabled: boolean;
    folders: string[];
    allowed_senders: string;
    lookback_days: number;
    max_emails_to_fetch: number;
}

const PROVIDERS = [
    { id: 'custom', name: 'Custom IMAP', host: '', port: 993 },
    { id: 'gmail', name: 'Gmail', host: 'imap.gmail.com', port: 993 },
];

const EmailIntegrationSettings: React.FC = () => {
    return (
        <FeatureGate
            feature="email_integration"
            fallback={
                <div className="bg-white dark:bg-gray-800 rounded-xl p-12 shadow-sm border border-gray-200 dark:border-gray-700">
                    <div className="text-center max-w-2xl mx-auto">
                        <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Mail className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                        </div>
                        <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">Business License Required</h3>
                        <p className="text-gray-600 dark:text-gray-300 mb-6">
                            Email integration allows you to automatically ingest expenses from your inbox - a powerful automation feature.
                            Upgrade to a business license to enable email integration and save time on manual entry.
                        </p>
                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 mb-6">
                            <h4 className="font-semibold text-gray-900 dark:text-white mb-3">With Business License, you get:</h4>
                            <ul className="text-left space-y-2 text-gray-700 dark:text-gray-300">
                                <li className="flex items-start">
                                    <span className="text-blue-600 mr-2">✓</span>
                                    <span>Automatic expense ingestion from email</span>
                                </li>
                                <li className="flex items-start">
                                    <span className="text-blue-600 mr-2">✓</span>
                                    <span>Support for Gmail, Outlook, and custom IMAP</span>
                                </li>
                                <li className="flex items-start">
                                    <span className="text-blue-600 mr-2">✓</span>
                                    <span>AI-powered expense classification</span>
                                </li>
                                <li className="flex items-start">
                                    <span className="text-blue-600 mr-2">✓</span>
                                    <span>Secure and encrypted connection</span>
                                </li>
                            </ul>
                        </div>
                        <div className="flex justify-center space-x-4">
                            <ProfessionalButton
                                onClick={() => window.location.href = '/settings?tab=license'}
                                variant="gradient"
                            >
                                Activate Business License
                            </ProfessionalButton>
                            <ProfessionalButton
                                variant="outline"
                                onClick={() => window.open('https://docs.example.com/email-integration', '_blank')}
                            >
                                Learn More
                            </ProfessionalButton>
                        </div>
                    </div>
                </div>
            }
        >
            <EmailIntegrationSettingsContent />
        </FeatureGate>
    );
};

const EmailIntegrationSettingsContent: React.FC = () => {
    const { t } = useTranslation();
    const [config, setConfig] = useState<EmailConfig>({
        imap_host: '',
        imap_port: 993,
        username: '',
        password: '',
        enabled: false,
        folders: ['INBOX'],
        allowed_senders: '',
        lookback_days: 30,
        max_emails_to_fetch: 100,
    });
    const [loading, setLoading] = useState(false);
    const [testing, setTesting] = useState(false);
    const [syncing, setSyncing] = useState(false);
    const [testResult, setTestResult] = useState<{ success: boolean, message: string } | null>(null);
    const [hasExistingPassword, setHasExistingPassword] = useState(false);

    useEffect(() => {
        // Check if there's an ongoing sync from localStorage
        const syncState = localStorage.getItem('email_sync_state');
        if (syncState) {
            const { timestamp } = JSON.parse(syncState);
            // If sync was started less than 5 minutes ago, assume it might still be running
            if (Date.now() - timestamp < 5 * 60 * 1000) {
                setSyncing(true);
                // Poll to check if sync is complete
                // checkSyncStatus(); // Handled by useEffect now
            } else {
                // Clear stale sync state
                localStorage.removeItem('email_sync_state');
            }
        }
        fetchConfig();
    }, []);

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (syncing) {
            interval = setInterval(async () => {
                try {
                    const data = await api.get<{ status: string, message: string, downloaded: number, processed: number }>('/email-integration/sync/status');

                    if (data.status === 'completed') {
                        setSyncing(false);
                        toast.success(data.message || t('emailIntegration.syncComplete'));
                        localStorage.removeItem('email_sync_state');
                    } else if (data.status === 'failed') {
                        setSyncing(false);
                        toast.error(data.message || t('emailIntegration.syncFailed'));
                        localStorage.removeItem('email_sync_state');
                    }
                    // If running or starting, just keep polling
                } catch (error) {
                    console.error('Error checking sync status:', error);
                }
            }, 2000);
        }
        return () => clearInterval(interval);
    }, [syncing]);

    const fetchConfig = async () => {
        setLoading(true);
        try {
            const data = await api.get<EmailConfig>('/email-integration/config');
            setConfig(prev => ({ ...prev, ...data, password: '' })); // Don't show password
            // Check if password exists in the saved config
            setHasExistingPassword(!!data.username); // If username exists, assume password exists too
        } catch (error) {
            console.error('Failed to fetch config', error);
            // toast.error("Failed to load email settings");
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (field: keyof EmailConfig, value: any) => {
        setConfig(prev => ({ ...prev, [field]: value }));
        // If password is being changed, mark that we have a new password
        if (field === 'password' && value) {
            setHasExistingPassword(true);
        }
    };

    const handleSave = async () => {
        setLoading(true);
        setTestResult(null);
        try {
            await api.post('/email-integration/config', config);
            toast.success(t('settings.save_success'));
            // After save, mark that password exists
            setHasExistingPassword(true);
        } catch (error) {
            toast.error(getErrorMessage(error, (k) => k));
        } finally {
            setLoading(false);
        }
    };

    const handleTestConnection = async () => {
        setTesting(true);
        setTestResult(null);
        try {
            // If password field is empty but we have an existing password, 
            // the backend will use the saved one
            await api.post('/email-integration/test', config);
            setTestResult({ success: true, message: t('emailIntegration.connectionSuccessful') });
            toast.success(t('emailIntegration.connectionSuccessful'));
        } catch (error) {
            const msg = getErrorMessage(error, (k) => k);
            setTestResult({ success: false, message: msg });
            toast.error(t('emailIntegration.connectionFailed'));
        } finally {
            setTesting(false);
        }
    };

    const handleSync = async () => {
        setSyncing(true);
        // Store sync state in localStorage
        localStorage.setItem('email_sync_state', JSON.stringify({ timestamp: Date.now() }));

        try {
            await api.post('/email-integration/sync');
            toast.info(t('emailIntegration.syncStarted'));
        } catch (error) {
            setSyncing(false);
            localStorage.removeItem('email_sync_state');
            toast.error(getErrorMessage(error, (k) => k));
        }
    };

    return (
        <ProfessionalCard variant="elevated">
            <ProfessionalCardHeader>
                <ProfessionalCardTitle className="flex items-center gap-2">
                    <Mail className="h-5 w-5 text-primary" />
                    {t('emailIntegration.title')}
                </ProfessionalCardTitle>
                <p className="text-sm text-muted-foreground">
                    {t('emailIntegration.description')}
                </p>
            </ProfessionalCardHeader>
            <ProfessionalCardContent className="space-y-6">

                {testResult && (
                    <div className={`p-4 rounded-xl border flex items-start gap-3 ${testResult.success
                        ? 'bg-green-50/50 border-green-200/50 text-green-800'
                        : 'bg-red-50/50 border-red-200/50 text-red-800'
                        }`}>
                        {testResult.success ? (
                            <CheckCircle2 className="h-5 w-5 mt-0.5 shrink-0" />
                        ) : (
                            <AlertCircle className="h-5 w-5 mt-0.5 shrink-0" />
                        )}
                        <div>
                            <h4 className="font-semibold text-sm">{testResult.success ? "Success" : "Error"}</h4>
                            <p className="text-sm font-medium leading-relaxed opacity-90">{testResult.message}</p>
                        </div>
                    </div>
                )}

                <div className="flex items-center justify-between p-4 bg-muted/20 rounded-xl border border-border/50">
                    <Label htmlFor="email-enabled" className="text-base font-medium flex-1 cursor-pointer">
                        {t('emailIntegration.enable')}
                    </Label>
                    <Switch
                        id="email-enabled"
                        checked={config.enabled}
                        onCheckedChange={(checked) => handleChange('enabled', checked)}
                    />
                </div>

                <div className="space-y-2">
                    <Label>{t('emailIntegration.serviceProvider')}</Label>
                    <Select
                        value={PROVIDERS.find(p => p.host === config.imap_host)?.id || 'custom'}
                        onValueChange={(value) => {
                            const provider = PROVIDERS.find(p => p.id === value);
                            if (provider) {
                                if (value === 'custom') {
                                    // Clear host when custom is selected so user can enter their own
                                    setConfig(prev => ({
                                        ...prev,
                                        imap_host: '',
                                        imap_port: 993
                                    }));
                                } else {
                                    // Set predefined provider settings
                                    setConfig(prev => ({
                                        ...prev,
                                        imap_host: provider.host,
                                        imap_port: provider.port
                                    }));
                                }
                            }
                        }}
                        disabled={loading}
                    >
                        <SelectTrigger className="h-10">
                            <SelectValue placeholder={t('emailIntegration.selectProvider')} />
                        </SelectTrigger>
                        <SelectContent>
                            {PROVIDERS.map(provider => (
                                <SelectItem key={provider.id} value={provider.id}>
                                    {provider.name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                {config.imap_host === 'imap.gmail.com' && (
                    <div className="p-4 bg-blue-50/50 border border-blue-200/50 rounded-xl text-blue-800 flex items-start gap-3">
                        <AlertCircle className="h-5 w-5 mt-0.5 shrink-0 text-blue-600" />
                        <div>
                            <h4 className="font-semibold text-sm mb-1">{t('emailIntegration.gmailAlert.title')}</h4>
                            <div className="text-sm opacity-90 space-y-1">
                                <p>{t('emailIntegration.gmailAlert.description')}</p>
                                <p>1. {t('emailIntegration.gmailAlert.step1')}</p>
                                <p>2. <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="underline font-medium hover:text-blue-900">{t('emailIntegration.gmailAlert.step2')}</a></p>
                                <p>3. {t('emailIntegration.gmailAlert.step3')}</p>
                            </div>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <ProfessionalInput
                        id="imap_host"
                        label={t('emailIntegration.imapHost')}
                        placeholder="imap.gmail.com"
                        value={config.imap_host}
                        onChange={(e) => handleChange('imap_host', e.target.value)}
                        disabled={loading}
                        leftIcon={<Globe className="w-4 h-4 text-muted-foreground" />}
                    />

                    <ProfessionalInput
                        id="imap_port"
                        type="number"
                        label={t('emailIntegration.imapPort')}
                        value={config.imap_port}
                        onChange={(e) => handleChange('imap_port', parseInt(e.target.value))}
                        disabled={loading}
                        leftIcon={<Hash className="w-4 h-4 text-muted-foreground" />}
                    />

                    <ProfessionalInput
                        id="username"
                        label={t('emailIntegration.username')}
                        value={config.username}
                        onChange={(e) => handleChange('username', e.target.value)}
                        disabled={loading}
                        leftIcon={<User className="w-4 h-4 text-muted-foreground" />}
                    />

                    <ProfessionalInput
                        id="password"
                        type="password"
                        label={t('emailIntegration.password')}
                        value={config.password}
                        onChange={(e) => handleChange('password', e.target.value)}
                        placeholder={config.password ? "********" : t('emailIntegration.passwordPlaceholder')}
                        disabled={loading}
                        helperText={t('emailIntegration.passwordHint')}
                        leftIcon={<Key className="w-4 h-4 text-muted-foreground" />}
                    />
                </div>

                <ProfessionalInput
                    id="allowed_senders"
                    label={t('emailIntegration.allowedSenders')}
                    value={config.allowed_senders}
                    onChange={(e) => handleChange('allowed_senders', e.target.value)}
                    placeholder={t('emailIntegration.allowedSendersPlaceholder')}
                    disabled={loading}
                    helperText={t('emailIntegration.allowedSendersHint')}
                    leftIcon={<List className="w-4 h-4 text-muted-foreground" />}
                />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <ProfessionalInput
                        id="lookback_days"
                        type="number"
                        min={1}
                        max={365}
                        label={t('emailIntegration.lookbackDays')}
                        value={config.lookback_days}
                        onChange={(e) => handleChange('lookback_days', parseInt(e.target.value))}
                        disabled={loading}
                        helperText={t('emailIntegration.lookbackDaysHint')}
                        leftIcon={<Clock className="w-4 h-4 text-muted-foreground" />}
                    />

                    <ProfessionalInput
                        id="max_emails_to_fetch"
                        type="number"
                        min={1}
                        max={1000}
                        label="Max Emails to Fetch per Sync"
                        value={config.max_emails_to_fetch}
                        onChange={(e) => handleChange('max_emails_to_fetch', parseInt(e.target.value))}
                        disabled={loading}
                        helperText="Limit the number of emails to process in a single sync. A lower number can prevent timeouts on slow servers."
                        leftIcon={<Server className="w-4 h-4 text-muted-foreground" />}
                    />
                </div>

                <div className="flex flex-wrap gap-4 pt-6 border-t border-border/50">
                    <ProfessionalButton
                        onClick={handleSave}
                        loading={loading}
                        disabled={loading || testing}
                        leftIcon={<Save className="h-4 w-4" />}
                        variant="gradient"
                    >
                        {t('emailIntegration.saveSettings')}
                    </ProfessionalButton>

                    <ProfessionalButton
                        variant="outline"
                        onClick={handleTestConnection}
                        loading={testing}
                        disabled={loading || testing || !config.imap_host || !config.username}
                        leftIcon={<CheckCircle2 className="h-4 w-4" />}
                    >
                        {t('emailIntegration.testConnection')}
                    </ProfessionalButton>

                    <ProfessionalButton
                        variant="secondary"
                        onClick={handleSync}
                        loading={syncing}
                        disabled={loading || testing || syncing || !config.enabled}
                        leftIcon={<RefreshCw className="h-4 w-4" />}
                    >
                        {t('emailIntegration.syncNow')}
                    </ProfessionalButton>
                </div>
            </ProfessionalCardContent>
        </ProfessionalCard>
    );
};

export default EmailIntegrationSettings;
