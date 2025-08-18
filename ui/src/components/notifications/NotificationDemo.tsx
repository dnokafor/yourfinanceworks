import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function NotificationDemo() {
  const addNotification = (window as any).addAINotification;

  const testNotifications = () => {
    // Test processing notification
    addNotification?.('processing', 'Processing Invoice PDF', 'Analyzing invoice_001.pdf with AI...');
    
    // Test success notification after 2 seconds
    setTimeout(() => {
      addNotification?.('success', 'Invoice PDF Processed', 'Successfully extracted data from invoice_001.pdf');
    }, 2000);
    
    // Test error notification after 4 seconds
    setTimeout(() => {
      addNotification?.('error', 'Bank Statement Processing Failed', 'Failed to process statement_002.pdf: Connection timeout');
    }, 4000);
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Notification Bell Demo</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-4">
          Click the button below to test the notification bell system with sample AI processing notifications.
        </p>
        <Button onClick={testNotifications} className="w-full">
          Test Notifications
        </Button>
      </CardContent>
    </Card>
  );
}