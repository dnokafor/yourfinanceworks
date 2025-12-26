import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Trophy, Settings, AlertTriangle, Info } from 'lucide-react';
import { useGamification } from '@/hooks/useGamification';
import { useTranslation } from 'react-i18next';
import { DataRetentionPolicy, NotificationFrequency } from '@/types/gamification';
import { toast } from 'sonner';

export function GamificationToggle() {
  const { t } = useTranslation();
  const { isEnabled, loading, enable, disable } = useGamification();
  const [showDialog, setShowDialog] = useState(false);
  const [isEnabling, setIsEnabling] = useState(false);
  const [dataRetentionPolicy, setDataRetentionPolicy] = useState<DataRetentionPolicy>(DataRetentionPolicy.PRESERVE);

  const handleToggle = async (enabled: boolean) => {
    if (enabled) {
      setIsEnabling(true);
      setShowDialog(true);
    } else {
      setIsEnabling(false);
      setShowDialog(true);
    }
  };

  const handleConfirm = async () => {
    try {
      if (isEnabling) {
        await enable({
          data_retention_policy: dataRetentionPolicy,
          preferences: {
            features: {
              points: true,
              achievements: true,
              streaks: true,
              challenges: true,
              social: false,
              notifications: true
            },
            privacy: {
              shareAchievements: false,
              showOnLeaderboard: false,
              allowFriendRequests: false
            },
            notifications: {
              streakReminders: true,
              achievementCelebrations: true,
              challengeUpdates: true,
              frequency: NotificationFrequency.DAILY
            }
          }
        });
        toast.success(t('settings.gamification.notifications.enabled_success'));
        // Refresh page to reload gamification state
        window.location.reload();
      } else {
        await disable({
          data_retention_policy: dataRetentionPolicy
        });
        toast.success(t('settings.gamification.notifications.disabled_success'));
        // Refresh page to reload gamification state
        window.location.reload();
      }
      setShowDialog(false);
    } catch (error) {
      console.error('Error toggling gamification:', error);
      toast.error(t('settings.gamification.notifications.toggle_error', { action: isEnabling ? 'enable' : 'disable' }));
    }
  };

  return (
    <>
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <Trophy className="h-4 w-4 text-yellow-500" />
          <span className="text-sm font-medium">{t('settings.gamification.title')}</span>
          <Badge variant={isEnabled ? "default" : "secondary"} className="text-xs">
            {isEnabled ? t('settings.gamification.enabled') : t('settings.gamification.disabled')}
          </Badge>
        </div>
        <Switch
          checked={isEnabled}
          onCheckedChange={handleToggle}
          disabled={loading}
        />
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              {isEnabling ? (
                <>
                  <Trophy className="h-5 w-5 text-yellow-500" />
                  <span>{t('settings.gamification.toggle_title')}</span>
                </>
              ) : (
                <>
                  <Settings className="h-5 w-5 text-gray-500" />
                  <span>{t('settings.gamification.disable_title')}</span>
                </>
              )}
            </DialogTitle>
            <DialogDescription>
              {isEnabling ? (
                <>
                  {t('settings.gamification.enable_description')}
                </>
              ) : (
                <>
                  {t('settings.gamification.disable_description')}
                </>
              )}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Data Retention Policy */}
            <div className="space-y-2">
              <Label htmlFor="retention-policy">{t('settings.gamification.data_retention_policy')}</Label>
              <Select
                value={dataRetentionPolicy}
                onValueChange={(value) => setDataRetentionPolicy(value as DataRetentionPolicy)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={DataRetentionPolicy.PRESERVE}>
                    <div className="space-y-1">
                      <div className="font-medium">{t('settings.gamification.preserve_data.label')}</div>
                      <div className="text-xs text-gray-600">
                        {t('settings.gamification.preserve_data.description')}
                      </div>
                    </div>
                  </SelectItem>
                  <SelectItem value={DataRetentionPolicy.ARCHIVE}>
                    <div className="space-y-1">
                      <div className="font-medium">{t('settings.gamification.archive_data.label')}</div>
                      <div className="text-xs text-gray-600">
                        {t('settings.gamification.archive_data.description')}
                      </div>
                    </div>
                  </SelectItem>
                  <SelectItem value={DataRetentionPolicy.DELETE}>
                    <div className="space-y-1">
                      <div className="font-medium">{t('settings.gamification.delete_data.label')}</div>
                      <div className="text-xs text-gray-600">
                        {t('settings.gamification.delete_data.description')}
                      </div>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Warning for delete policy */}
            {dataRetentionPolicy === DataRetentionPolicy.DELETE && (
              <div className="flex items-start space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-red-800">{t('settings.gamification.warning')}</p>
                  <p className="text-red-600">
                    {t('settings.gamification.delete_warning')}
                  </p>
                </div>
              </div>
            )}

            {/* Info about enabling */}
            {isEnabling && (
              <div className="flex items-start space-x-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <Info className="h-4 w-4 text-blue-500 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-blue-800">{t('settings.gamification.what_you_get')}</p>
                  <ul className="text-blue-600 mt-1 space-y-1">
                    <li>• {t('settings.gamification.benefits.points')}</li>
                    <li>• {t('settings.gamification.benefits.achievements')}</li>
                    <li>• {t('settings.gamification.benefits.streaks')}</li>
                    <li>• {t('settings.gamification.benefits.challenges')}</li>
                    <li>• {t('settings.gamification.benefits.wellness')}</li>
                  </ul>
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              {t('common.cancel')}
            </Button>
            <Button onClick={handleConfirm}>
              {isEnabling ? t('settings.gamification.toggle_title') : t('settings.gamification.disable_title')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}