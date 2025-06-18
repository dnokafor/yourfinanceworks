import React, { useState, useEffect } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { settingsApi } from "@/lib/api";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const Settings = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [companyInfo, setCompanyInfo] = useState({
    name: "Your Company",
    email: "contact@yourcompany.com",
    phone: "(555) 123-4567",
    address: "123 Business Avenue, Suite 100, New York, NY 10001",
    tax_id: "12-3456789",
    logo: "",
  });

  const [invoiceSettings, setInvoiceSettings] = useState({
    prefix: "INV-",
    next_number: "0001",
    terms: "Payment due within 30 days from the date of invoice.\nLate payments are subject to a 1.5% monthly finance charge.",
    notes: "Thank you for your business!",
    send_copy: true,
    auto_reminders: true,
  });

  const [emailSettings, setEmailSettings] = useState({
    provider: "aws_ses",
    from_name: "Your Company",
    from_email: "noreply@yourcompany.com",
    enabled: false,
    // AWS SES
    aws_access_key_id: "",
    aws_secret_access_key: "",
    aws_region: "us-east-1",
    // Azure Email Services
    azure_connection_string: "",
    // Mailgun
    mailgun_api_key: "",
    mailgun_domain: "",
  });

  // Fetch settings when component mounts
  useEffect(() => {
    const fetchSettings = async () => {
      setLoading(true);
      try {
        const settings = await settingsApi.getSettings();
        
        // Update state with fetched settings
        if (settings.company_info) {
          setCompanyInfo({
            name: settings.company_info.name || companyInfo.name,
            email: settings.company_info.email || companyInfo.email,
            phone: settings.company_info.phone || companyInfo.phone,
            address: settings.company_info.address || companyInfo.address,
            tax_id: settings.company_info.tax_id || companyInfo.tax_id,
            logo: settings.company_info.logo || companyInfo.logo,
          });
        }
        
        if (settings.invoice_settings) {
          setInvoiceSettings({
            prefix: settings.invoice_settings.prefix || invoiceSettings.prefix,
            next_number: settings.invoice_settings.next_number || invoiceSettings.next_number,
            terms: settings.invoice_settings.terms || invoiceSettings.terms,
            notes: settings.invoice_settings.notes || invoiceSettings.notes,
            send_copy: settings.invoice_settings.send_copy ?? invoiceSettings.send_copy,
            auto_reminders: settings.invoice_settings.auto_reminders ?? invoiceSettings.auto_reminders,
          });
        }

        // Try to fetch email settings
        try {
          const emailConfig = await fetch('/api/email/config', {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
          });
          
          if (emailConfig.ok) {
            const emailData = await emailConfig.json();
            setEmailSettings({
              provider: emailData.provider || emailSettings.provider,
              from_name: emailData.from_name || emailSettings.from_name,
              from_email: emailData.from_email || emailSettings.from_email,
              enabled: emailData.enabled ?? emailSettings.enabled,
              aws_access_key_id: emailData.aws_access_key_id || emailSettings.aws_access_key_id,
              aws_secret_access_key: emailData.aws_secret_access_key || emailSettings.aws_secret_access_key,
              aws_region: emailData.aws_region || emailSettings.aws_region,
              azure_connection_string: emailData.azure_connection_string || emailSettings.azure_connection_string,
              mailgun_api_key: emailData.mailgun_api_key || emailSettings.mailgun_api_key,
              mailgun_domain: emailData.mailgun_domain || emailSettings.mailgun_domain,
            });
          }
        } catch (error) {
          console.log("Email settings not configured yet");
        }
      } catch (error) {
        console.error("Failed to fetch settings:", error);
        toast.error("Failed to load settings");
      } finally {
        setLoading(false);
      }
    };
    
    fetchSettings();
  }, []);

  const handleCompanyChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setCompanyInfo((prev) => ({ ...prev, [name]: value }));
  };

  const handleInvoiceChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setInvoiceSettings((prev) => ({ ...prev, [name]: value }));
  };

  const handleToggleChange = (name: string, checked: boolean) => {
    setInvoiceSettings((prev) => ({ ...prev, [name]: checked }));
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setEmailSettings((prev) => ({ ...prev, [name]: value }));
  };

  const handleEmailProviderChange = (provider: string) => {
    setEmailSettings((prev) => ({ ...prev, provider }));
  };

  const handleEmailToggleChange = (name: string, checked: boolean) => {
    setEmailSettings((prev) => ({ ...prev, [name]: checked }));
  };

  const testEmailConfiguration = async () => {
    const testEmail = prompt("Enter email address to send test email to:");
    if (!testEmail) return;

    try {
      const response = await fetch('/api/email/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ test_email: testEmail }),
      });

      const result = await response.json();
      if (result.success) {
        toast.success(`Test email sent successfully to ${testEmail}`);
      } else {
        toast.error(`Failed to send test email: ${result.message}`);
      }
    } catch (error) {
      toast.error("Failed to send test email");
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Format data for API
      const settingsData = {
        company_info: {
          name: companyInfo.name,
          email: companyInfo.email,
          phone: companyInfo.phone,
          address: companyInfo.address,
          tax_id: companyInfo.tax_id,
          logo: companyInfo.logo
        },
        invoice_settings: {
          prefix: invoiceSettings.prefix,
          next_number: invoiceSettings.next_number,
          terms: invoiceSettings.terms,
          notes: invoiceSettings.notes,
          send_copy: invoiceSettings.send_copy,
          auto_reminders: invoiceSettings.auto_reminders
        }
      };
      
      // Send to API
      await settingsApi.updateSettings(settingsData);
      
      // Save email settings separately
      try {
        await fetch('/api/email/config', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify(emailSettings),
        });
      } catch (error) {
        console.log("Failed to save email settings:", error);
      }
      
      toast.success("Settings saved successfully!");
    } catch (error) {
      console.error("Failed to save settings:", error);
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center h-screen">
          <Loader2 className="h-8 w-8 animate-spin mr-2" />
          <p>Loading settings...</p>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="h-full space-y-6 fade-in">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Configure your account and preferences</p>
        </div>

        <Tabs defaultValue="company" className="slide-in">
          <TabsList className="grid w-full max-w-lg grid-cols-3">
            <TabsTrigger value="company">Company Info</TabsTrigger>
            <TabsTrigger value="invoices">Invoice Settings</TabsTrigger>
            <TabsTrigger value="email">Email Settings</TabsTrigger>
          </TabsList>
          
          <TabsContent value="company" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Company Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="name">Company Name</Label>
                    <Input 
                      id="name" 
                      name="name" 
                      value={companyInfo.name} 
                      onChange={handleCompanyChange} 
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="tax_id">Tax ID / EIN</Label>
                    <Input 
                      id="tax_id" 
                      name="tax_id" 
                      value={companyInfo.tax_id} 
                      onChange={handleCompanyChange} 
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input 
                      id="email" 
                      name="email" 
                      type="email" 
                      value={companyInfo.email} 
                      onChange={handleCompanyChange} 
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone</Label>
                    <Input 
                      id="phone" 
                      name="phone" 
                      value={companyInfo.phone} 
                      onChange={handleCompanyChange} 
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="address">Address</Label>
                  <Textarea 
                    id="address" 
                    name="address" 
                    rows={3} 
                    value={companyInfo.address} 
                    onChange={handleCompanyChange} 
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="logo">Company Logo</Label>
                  <Input 
                    id="logo" 
                    name="logo" 
                    type="file" 
                    accept="image/*" 
                  />
                  <p className="text-sm text-muted-foreground">Recommended size: 200x200px</p>
                </div>
                
                <div className="flex justify-end">
                  <Button onClick={handleSave} disabled={saving}>
                    {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Save Changes
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="invoices" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Invoice Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="prefix">Invoice Number Prefix</Label>
                    <Input 
                      id="prefix" 
                      name="prefix" 
                      value={invoiceSettings.prefix} 
                      onChange={handleInvoiceChange} 
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="next_number">Next Invoice Number</Label>
                    <Input 
                      id="next_number" 
                      name="next_number" 
                      value={invoiceSettings.next_number} 
                      onChange={handleInvoiceChange} 
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="terms">Default Terms & Conditions</Label>
                  <Textarea 
                    id="terms" 
                    name="terms" 
                    rows={4} 
                    value={invoiceSettings.terms} 
                    onChange={handleInvoiceChange} 
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="notes">Default Notes</Label>
                  <Textarea 
                    id="notes" 
                    name="notes" 
                    rows={2} 
                    value={invoiceSettings.notes} 
                    onChange={handleInvoiceChange} 
                  />
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="send_copy">Send Me a Copy</Label>
                      <p className="text-sm text-muted-foreground">Receive a copy of each invoice by email</p>
                    </div>
                    <Switch 
                      id="send_copy" 
                      checked={invoiceSettings.send_copy} 
                      onCheckedChange={(checked) => handleToggleChange('send_copy', checked)} 
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="auto_reminders">Automatic Reminders</Label>
                      <p className="text-sm text-muted-foreground">Send reminder emails for overdue invoices</p>
                    </div>
                    <Switch 
                      id="auto_reminders" 
                      checked={invoiceSettings.auto_reminders} 
                      onCheckedChange={(checked) => handleToggleChange('auto_reminders', checked)} 
                    />
                  </div>
                </div>
                
                <div className="flex justify-end">
                  <Button onClick={handleSave} disabled={saving}>
                    {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Save Changes
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="email" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Email Configuration</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="email_enabled">Enable Email Service</Label>
                    <p className="text-sm text-muted-foreground">Enable sending invoices via email</p>
                  </div>
                  <Switch 
                    id="email_enabled" 
                    checked={emailSettings.enabled} 
                    onCheckedChange={(checked) => handleEmailToggleChange('enabled', checked)} 
                  />
                </div>

                {emailSettings.enabled && (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="provider">Email Provider</Label>
                      <Select value={emailSettings.provider} onValueChange={handleEmailProviderChange}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select email provider" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="aws_ses">AWS SES</SelectItem>
                          <SelectItem value="azure_email">Azure Email Services</SelectItem>
                          <SelectItem value="mailgun">Mailgun</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <Label htmlFor="from_name">From Name</Label>
                        <Input 
                          id="from_name" 
                          name="from_name" 
                          value={emailSettings.from_name} 
                          onChange={handleEmailChange} 
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="from_email">From Email</Label>
                        <Input 
                          id="from_email" 
                          name="from_email" 
                          type="email" 
                          value={emailSettings.from_email} 
                          onChange={handleEmailChange} 
                        />
                      </div>
                    </div>

                    {emailSettings.provider === "aws_ses" && (
                      <div className="space-y-4 p-4 border rounded-lg">
                        <h4 className="font-medium">AWS SES Configuration</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="aws_access_key_id">Access Key ID</Label>
                            <Input 
                              id="aws_access_key_id" 
                              name="aws_access_key_id" 
                              type="password"
                              value={emailSettings.aws_access_key_id} 
                              onChange={handleEmailChange} 
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="aws_secret_access_key">Secret Access Key</Label>
                            <Input 
                              id="aws_secret_access_key" 
                              name="aws_secret_access_key" 
                              type="password"
                              value={emailSettings.aws_secret_access_key} 
                              onChange={handleEmailChange} 
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="aws_region">AWS Region</Label>
                          <Select value={emailSettings.aws_region} onValueChange={(value) => setEmailSettings(prev => ({ ...prev, aws_region: value }))}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="us-east-1">US East (N. Virginia)</SelectItem>
                              <SelectItem value="us-west-2">US West (Oregon)</SelectItem>
                              <SelectItem value="eu-west-1">EU (Ireland)</SelectItem>
                              <SelectItem value="ap-southeast-1">Asia Pacific (Singapore)</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    )}

                    {emailSettings.provider === "azure_email" && (
                      <div className="space-y-4 p-4 border rounded-lg">
                        <h4 className="font-medium">Azure Email Services Configuration</h4>
                        <div className="space-y-2">
                          <Label htmlFor="azure_connection_string">Connection String</Label>
                          <Input 
                            id="azure_connection_string" 
                            name="azure_connection_string" 
                            type="password"
                            value={emailSettings.azure_connection_string} 
                            onChange={handleEmailChange} 
                          />
                        </div>
                      </div>
                    )}

                    {emailSettings.provider === "mailgun" && (
                      <div className="space-y-4 p-4 border rounded-lg">
                        <h4 className="font-medium">Mailgun Configuration</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="mailgun_api_key">API Key</Label>
                            <Input 
                              id="mailgun_api_key" 
                              name="mailgun_api_key" 
                              type="password"
                              value={emailSettings.mailgun_api_key} 
                              onChange={handleEmailChange} 
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="mailgun_domain">Domain</Label>
                            <Input 
                              id="mailgun_domain" 
                              name="mailgun_domain" 
                              value={emailSettings.mailgun_domain} 
                              onChange={handleEmailChange} 
                            />
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="flex justify-between">
                      <Button 
                        type="button" 
                        variant="outline" 
                        onClick={testEmailConfiguration}
                      >
                        Test Configuration
                      </Button>
                      <Button onClick={handleSave} disabled={saving}>
                        {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Save Email Settings
                      </Button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
};

export default Settings;
