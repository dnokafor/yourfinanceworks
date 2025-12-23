import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Zap, Target, TrendingUp, Calendar, CheckCircle, Plus } from 'lucide-react';
import type { PointHistory } from '@/types/gamification';

const actionTypeIcons = {
  expense_added: Target,
  invoice_created: TrendingUp,
  receipt_uploaded: CheckCircle,
  budget_reviewed: Calendar,
  payment_recorded: Plus,
  category_assigned: CheckCircle
};

const actionTypeLabels = {
  expense_added: 'Expense Added',
  invoice_created: 'Invoice Created',
  receipt_uploaded: 'Receipt Uploaded',
  budget_reviewed: 'Budget Reviewed',
  payment_recorded: 'Payment Recorded',
  category_assigned: 'Category Assigned'
};

const actionTypeColors = {
  expense_added: 'text-blue-500',
  invoice_created: 'text-green-500',
  receipt_uploaded: 'text-orange-500',
  budget_reviewed: 'text-purple-500',
  payment_recorded: 'text-teal-500',
  category_assigned: 'text-pink-500'
};

interface RecentPointsHistoryProps {
  points: PointHistory[];
}

export function RecentPointsHistory({ points }: RecentPointsHistoryProps) {
  if (!points || points.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-5 w-5 text-blue-500" />
            <span>Recent Points</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Zap className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Recent Activity</h3>
            <p className="text-gray-600">
              Start tracking expenses or creating invoices to earn your first points!
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const totalRecentPoints = points.reduce((sum, point) => sum + point.points_awarded, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Zap className="h-5 w-5 text-blue-500" />
            <span>Recent Points</span>
          </div>
          <Badge variant="outline" className="text-blue-600">
            +{totalRecentPoints} XP
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {points.slice(0, 8).map((point) => {
            const IconComponent = actionTypeIcons[point.action_type as keyof typeof actionTypeIcons] || Target;
            const actionLabel = actionTypeLabels[point.action_type as keyof typeof actionTypeLabels] || point.action_type;
            const iconColor = actionTypeColors[point.action_type as keyof typeof actionTypeColors] || 'text-gray-500';
            
            return (
              <div key={point.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-white rounded-lg">
                    <IconComponent className={`h-4 w-4 ${iconColor}`} />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{actionLabel}</p>
                    <p className="text-xs text-gray-600">
                      {new Date(point.created_at).toLocaleDateString()} at{' '}
                      {new Date(point.created_at).toLocaleTimeString([], { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </p>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="flex items-center space-x-1">
                    <Zap className="h-3 w-3 text-blue-500" />
                    <span className="text-sm font-bold text-blue-600">
                      +{point.points_awarded}
                    </span>
                  </div>
                  
                  {/* Show bonus breakdown if applicable */}
                  {(point.streak_multiplier > 1 || point.accuracy_bonus > 0 || point.completeness_bonus > 0) && (
                    <div className="flex items-center space-x-1 text-xs text-gray-500 mt-1">
                      <span>{point.base_points} base</span>
                      {point.streak_multiplier > 1 && (
                        <span className="text-orange-600">
                          ×{point.streak_multiplier.toFixed(1)} streak
                        </span>
                      )}
                      {point.accuracy_bonus > 0 && (
                        <span className="text-green-600">
                          +{point.accuracy_bonus} accuracy
                        </span>
                      )}
                      {point.completeness_bonus > 0 && (
                        <span className="text-purple-600">
                          +{point.completeness_bonus} complete
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
        
        {points.length > 8 && (
          <div className="text-center mt-4">
            <p className="text-sm text-gray-600">
              Showing {Math.min(8, points.length)} of {points.length} recent activities
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}