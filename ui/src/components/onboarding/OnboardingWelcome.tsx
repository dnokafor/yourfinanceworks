import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Play, BookOpen, X } from 'lucide-react';
import { useOnboarding } from './OnboardingProvider';
import { useTranslation } from 'react-i18next';

interface OnboardingWelcomeProps {
  open: boolean;
  onClose: () => void;
}

export function OnboardingWelcome({ open, onClose }: OnboardingWelcomeProps) {
  const { startTour, tours } = useOnboarding();
  const { t } = useTranslation();

  const handleStartTour = (tourId: string) => {
    onClose();
    startTour(tourId);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-center">
            Welcome to Invoice Manager! 🎉
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          <div className="text-center">
            <p className="text-muted-foreground">
              Let's get you started with a quick tour of the key features
            </p>
          </div>
          
          <div className="grid gap-4">
            {tours.map((tour) => (
              <Card key={tour.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-primary/10 rounded-lg">
                        <BookOpen className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-semibold">{tour.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {tour.steps.length} steps • ~{Math.ceil(tour.steps.length * 0.5)} minutes
                        </p>
                      </div>
                    </div>
                    <Button onClick={() => handleStartTour(tour.id)} size="sm">
                      <Play className="h-4 w-4 mr-1" />
                      Start Tour
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          
          <div className="flex justify-center gap-3">
            <Button variant="outline" onClick={onClose}>
              <X className="h-4 w-4 mr-1" />
              Skip for now
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}