import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Flame, Calendar, Target, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';
import type { UserStreak, HabitType } from '@/types/gamification';

const habitTypeLabels = {
  daily_expense_tracking: 'Daily Expense Tracking',
  weekly_budget_review: 'Weekly Budget Review',
  invoice_follow_up: 'Invoice Follow-up',
  receipt_documentation: 'Receipt Documentation'
};

const habitTypeIcons = {
  daily_expense_tracking: Target,
  weekly_budget_review: TrendingUp,
  invoice_follow_up: Calendar,
  receipt_documentation: CheckCircle
};

const habitTypeColors = {
  daily_expense_tracking: 'text-blue-500',
  weekly_budget_review: 'text-green-500',
  invoice_follow_up: 'text-purple-500',
  receipt_documentation: 'text-orange-500'
};

interface StreakDisplayProps {
  streak: UserStreak;
  compact?: boolean;
}

export function StreakDisplay({ streak, compact = false }: StreakDisplayProps) {
  const habitLabel = habitTypeLabels[streak.habit_type as keyof typeof habitTypeLabels] || streak.habit_type;
  const IconComponent = habitTypeIcons[streak.habit_type as keyof typeof habitTypeIcons] || Target;
  const iconColor = habitTypeColors[streak.habit_type as keyof typeof habitTypeColors] || 'text-gray-500';
  
  const isActive = streak.is_active;
  const daysSinceActivity = streak.last_activity_date 
    ? Math.floor((new Date().getTime() - new Date(streak.last_activity_date).getTime()) / (1000 * 60 * 60 * 24))
    : 0;
  
  // Determine risk level based on habit type and days since activity
  const getRiskLevel = () => {
    if (!isActive) return 'broken';
    if (daysSinceActivity === 0) return 'safe';
    if (streak.habit_type === 'daily_expense_tracking' && daysSinceActivity >= 1) return 'high_risk';
    if (streak.habit_type === 'weekly_budget_review' && daysSinceActivity >= 7) return 'high_risk';
    if (daysSinceActivity >= 3) return 'medium_risk';
    return 'low_risk';
  };

  const riskLevel = getRiskLevel();
  
  const riskColors = {
    safe: 'text-green-600 bg-green-50 border-green-200',
    low_risk: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    medium_risk: 'text-orange-600 bg-orange-50 border-orange-200',
    high_risk: 'text-red-600 bg-red-50 border-red-200',
    broken: 'text-gray-600 bg-gray-50 border-gray-200'
  };

  const riskLabels = {
    safe: 'On Track',
    low_risk: 'Low Risk',
    medium_risk: 'At Risk',
    high_risk: 'High Risk',
    broken: 'Broken'
  };

  if (compact) {
    return (
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${isActive ? 'bg-orange-100' : 'bg-gray-100'}`}>
            {isActive ? (
              <Flame className="h-4 w-4 text-orange-500" />
            ) : (
              <IconComponent className={`h-4 w-4 ${iconColor}`} />
            )}
          </div>
          <div>
            <p className="text-sm font-medium">{habitLabel}</p>
            <p className="text-xs text-gray-600">
              {isActive ? `${streak.current_length} day streak` : 'Streak broken'}
            </p>
          </div>
        </div>
        <div className="text-right">
          <Badge variant="outline" className={`text-xs ${riskColors[riskLevel]}`}>
            {riskLabels[riskLevel]}
          </Badge>
          {streak.longest_length > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Best: {streak.longest_length} days
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <Card className={`${riskColors[riskLevel]} border-2`}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <IconComponent className={`h-5 w-5 ${iconColor}`} />
            <span>{habitLabel}</span>
          </div>
          <Badge variant="outline" className={riskColors[riskLevel]}>
            {riskLabels[riskLevel]}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Streak */}
        <div className="text-center">
          <div className="flex items-center justify-center space-x-2 mb-2">
            <Flame className={`h-8 w-8 ${isActive ? 'text-orange-500' : 'text-gray-400'}`} />
            <span className="text-3xl font-bold">
              {isActive ? streak.current_length : 0}
            </span>
          </div>
          <p className="text-sm text-gray-600">
            {isActive ? 'Current Streak' : 'Streak Broken'}
          </p>
        </div>

        {/* Progress to next milestone */}
        {isActive && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Next Milestone</span>
              <span className="font-medium">
                {streak.current_length < 7 ? '7 days' : 
                 streak.current_length < 30 ? '30 days' : 
                 streak.current_length < 90 ? '90 days' : '365 days'}
              </span>
            </div>
            <Progress 
              value={
                streak.current_length < 7 ? (streak.current_length / 7) * 100 :
                streak.current_length < 30 ? ((streak.current_length - 7) / 23) * 100 :
                streak.current_length < 90 ? ((streak.current_length - 30) / 60) * 100 :
                ((streak.current_length - 90) / 275) * 100
              } 
              className="h-2" 
            />
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 pt-4 border-t">
          <div className="text-center">
            <p className="text-lg font-bold text-blue-600">{streak.longest_length}</p>
            <p className="text-xs text-gray-600">Best Streak</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-bold text-purple-600">{streak.times_broken || 0}</p>
            <p className="text-xs text-gray-600">Times Broken</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-bold text-green-600">{daysSinceActivity}</p>
            <p className="text-xs text-gray-600">Days Since</p>
          </div>
        </div>

        {/* Last Activity */}
        {streak.last_activity_date && (
          <div className="text-center text-sm text-gray-600">
            Last activity: {new Date(streak.last_activity_date).toLocaleDateString()}
          </div>
        )}

        {/* Risk Warning */}
        {riskLevel === 'high_risk' && (
          <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
            <AlertTriangle className="h-4 w-4 text-red-500" />
            <div className="text-sm">
              <p className="font-medium text-red-800">Streak at risk!</p>
              <p className="text-red-600">
                {streak.habit_type === 'daily_expense_tracking' 
                  ? 'Track an expense today to keep your streak alive.'
                  : 'Complete this habit soon to maintain your streak.'
                }
              </p>
            </div>
          </div>
        )}

        {/* Encouragement for broken streaks */}
        {!isActive && (
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-3">
              Don't worry! Every expert was once a beginner. Start a new streak today.
            </p>
            <Button size="sm" variant="outline">
              Start New Streak
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}