import React, { useState, useEffect } from 'react';
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    CardDescription
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
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
    Loader2
} from "lucide-react";
import { toast } from "sonner";
import { api, getErrorMessage } from "@/lib/api";

interface EmailConfig {
    imap_host: string;
    imap_port: number;
    username: string;
    password?: string;
    enabled: boolean;
    folders: string[];
    allowed_senders: string;
    lookback_days: number;
}

const PROVIDERS = [
    { id: 'custom', name: 'Custom IMAP', host: '', port: 993 },
    { id: 'gmail', name: 'Gmail', host: 'imap.gmail.com', port: 993 },
    { id: 'outlook', name: 'Outlook / Office 365', host: 'outlook.office365.com', port: 993 },
    { id: 'yahoo', name: 'Yahoo Mail', host: 'imap.mail.yahoo.com', port: 993 },
];

const EmailIntegrationSettings: React.FC = () => {
    const [config, setConfig] = useState<EmailConfig>({
        imap_host: '',
        imap_port: 993,
        username: '',
        password: '',
        enabled: false,
        folders: ['INBOX'],
        allowed_senders: '',
        lookback_days: 30
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
                        toast.success(data.message || "Sync complete");
                        localStorage.removeItem('email_sync_state');
                    } else if (data.status === 'failed') {
                        setSyncing(false);
                        toast.error(data.message || "Sync failed");
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
            toast.success("Settings saved successfully");
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
            setTestResult({ success: true, message: "Connection successful!" });
            toast.success("Connection successful!");
        } catch (error) {
            const msg = getErrorMessage(error, (k) => k);
            setTestResult({ success: false, message: msg });
            toast.error("Connection failed");
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
            toast.info("Sync started in background...");
        } catch (error) {
            setSyncing(false);
            localStorage.removeItem('email_sync_state');
            toast.error(getErrorMessage(error, (k) => k));
        }
    };

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center gap-2">
                    <Mail className="h-5 w-5 text-primary" />
                    <CardTitle>Email Integration</CardTitle>
                </div>
                <CardDescription>
                    Configure IMAP settings to automatically ingest expenses from your email.
                    The system will scan for receipts and invoices in the specified folders.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">

                {testResult && (
                    <Alert variant={testResult.success ? "default" : "destructive"}>
                        {testResult.success ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                        <AlertTitle>{testResult.success ? "Success" : "Error"}</AlertTitle>
                        <AlertDescription>{testResult.message}</AlertDescription>
                    </Alert>
                )}

                <div className="flex items-center space-x-2">
                    <Switch
                        id="email-enabled"
                        checked={config.enabled}
                        onCheckedChange={(checked) => handleChange('enabled', checked)}
                    />
                    <Label htmlFor="email-enabled">Enable Email Integration</Label>
                </div>

                <div className="space-y-2">
                    <Label>Service Provider</Label>
                    <Select
                        value={PROVIDERS.find(p => p.host === config.imap_host)?.id || 'custom'}
                        onValueChange={(value) => {
                            const provider = PROVIDERS.find(p => p.id === value);
                            if (provider && value !== 'custom') {
                                setConfig(prev => ({
                                    ...prev,
                                    imap_host: provider.host,
                                    imap_port: provider.port
                                }));
                            }
                        }}
                        disabled={loading}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="Select a provider" />
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
                    <Alert className="bg-blue-50 border-blue-200 text-blue-800">
                        <AlertCircle className="h-4 w-4 text-blue-800" />
                        <AlertTitle>Gmail Configuration</AlertTitle>
                        <AlertDescription>
                            Gmail requires an <strong>App Password</strong> to connect via IMAP. Your regular password will not work.
                            <br />
                            1. Enable 2-Step Verification in your Google Account.
                            <br />
                            2. Go to <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="underline font-medium">App Passwords</a>.
                            <br />
                            3. Generate a new password for "Mail" and use it below.
                        </AlertDescription>
                    </Alert>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label htmlFor="imap_host">IMAP Host</Label>
                        <Input
                            id="imap_host"
                            placeholder="imap.gmail.com"
                            value={config.imap_host}
                            onChange={(e) => handleChange('imap_host', e.target.value)}
                            disabled={loading}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="imap_port">IMAP Port</Label>
                        <Input
                            id="imap_port"
                            type="number"
                            value={config.imap_port}
                            onChange={(e) => handleChange('imap_port', parseInt(e.target.value))}
                            disabled={loading}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="username">Username / Email</Label>
                        <Input
                            id="username"
                            value={config.username}
                            onChange={(e) => handleChange('username', e.target.value)}
                            disabled={loading}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="password">Password / App Password</Label>
                        <Input
                            id="password"
                            type="password"
                            value={config.password}
                            onChange={(e) => handleChange('password', e.target.value)}
                            placeholder={config.password ? "********" : "Enter new password"}
                            disabled={loading}
                        />
                        <p className="text-xs text-muted-foreground">For Gmail, use an App Password.</p>
                    </div>
                </div>

                <div className="space-y-2">
                    <Label htmlFor="allowed_senders">Allowed Senders (Optional)</Label>
                    <Input
                        id="allowed_senders"
                        value={config.allowed_senders}
                        onChange={(e) => handleChange('allowed_senders', e.target.value)}
                        placeholder="receipts@uber.com, billing@aws.com"
                        disabled={loading}
                    />
                    <p className="text-xs text-muted-foreground">Comma separated list of email addresses. Leave empty to allow all.</p>
                </div>

                <div className="space-y-2">
                    <Label htmlFor="lookback_days">Lookback Days</Label>
                    <Input
                        id="lookback_days"
                        type="number"
                        min={1}
                        max={365}
                        value={config.lookback_days}
                        onChange={(e) => handleChange('lookback_days', parseInt(e.target.value))}
                        disabled={loading}
                    />
                    <p className="text-xs text-muted-foreground">How many days back to search for emails (default: 30).</p>
                </div>

                <div className="flex flex-wrap gap-4 pt-4">
                    <Button
                        onClick={handleSave}
                        disabled={loading || testing}
                        className="gap-2"
                    >
                        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                        Save Settings
                    </Button>

                    <Button
                        variant="outline"
                        onClick={handleTestConnection}
                        disabled={loading || testing || !config.imap_host || !config.username}
                        className="gap-2"
                    >
                        {testing ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                        Test Connection
                    </Button>

                    <Button
                        variant="secondary"
                        onClick={handleSync}
                        disabled={loading || testing || syncing || !config.enabled}
                        className="gap-2"
                    >
                        {syncing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                        Sync Now
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
};

export default EmailIntegrationSettings;
