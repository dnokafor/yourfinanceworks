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
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="company">Company Info</TabsTrigger>
            <TabsTrigger value="invoices">Invoice Settings</TabsTrigger>
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
        </Tabs>
      </div>
    </AppLayout>
  );
};

export default Settings;
