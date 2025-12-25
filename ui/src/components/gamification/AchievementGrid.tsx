import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Award, Trophy, Star, Target, TrendingUp, Lock, RefreshCw } from 'lucide-react';
import { gamificationApi } from '@/lib/api';
import type { UserAchievement } from '@/types/gamification';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Button } from '@/components/ui/button';

const categoryIcons = {
  expense_tracking: Target,
  invoice_management: TrendingUp,
  habit_formation: Star,
  financial_health: Trophy,
  exploration: Award
};

const categoryColors = {
  expense_tracking: 'text-blue-500',
  invoice_management: 'text-green-500',
  habit_formation: 'text-purple-500',
  financial_health: 'text-yellow-500',
  exploration: 'text-pink-500'
};

const difficultyColors = {
  bronze: 'bg-amber-100 text-amber-800',
  silver: 'bg-gray-100 text-gray-800',
  gold: 'bg-yellow-100 text-yellow-800',
  platinum: 'bg-purple-100 text-purple-800'
};

interface AchievementCardProps {
  achievement: UserAchievement;
}

function AchievementCard({ achievement }: AchievementCardProps) {
  const IconComponent = categoryIcons[achievement.achievement.category as keyof typeof categoryIcons] || Award;
  const iconColor = categoryColors[achievement.achievement.category as keyof typeof categoryColors] || 'text-gray-500';
  const difficultyColor = difficultyColors[achievement.achievement.difficulty as keyof typeof difficultyColors] || 'bg-gray-100 text-gray-800';
  
  const isCompleted = achievement.is_completed;
  const progress = Math.round(achievement.progress * 100);

  return (
    <Card className={`transition-all duration-200 hover:shadow-md ${isCompleted ? 'ring-2 ring-green-200 bg-green-50' : ''}`}>
      <CardContent className="p-4">
        <div className="flex items-start space-x-3">
          <div className={`flex-shrink-0 p-2 rounded-lg ${isCompleted ? 'bg-green-100' : 'bg-gray-100'}`}>
            {isCompleted ? (
              <Trophy className="h-6 w-6 text-green-600" />
            ) : (
              <IconComponent className={`h-6 w-6 ${iconColor}`} />
            )}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-2">
              <h3 className={`font-medium text-sm ${isCompleted ? 'text-green-800' : 'text-gray-900'}`}>
                {achievement.achievement.name}
              </h3>
              <Badge variant="secondary" className={`text-xs ${difficultyColor}`}>
                {achievement.achievement.difficulty}
              </Badge>
            </div>
            
            <p className="text-xs text-gray-600 mb-3 line-clamp-2">
              {achievement.achievement.description}
            </p>
            
            {!isCompleted && (
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Progress</span>
                  <span className="font-medium">{progress}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
            )}
            
            {isCompleted && achievement.unlocked_at && (
              <div className="flex items-center space-x-1 text-xs text-green-600">
                <Trophy className="h-3 w-3" />
                <span>Unlocked {new Date(achievement.unlocked_at).toLocaleDateString()}</span>
              </div>
            )}
            
            {achievement.achievement.reward_xp > 0 && (
              <div className="flex items-center space-x-1 text-xs text-blue-600 mt-2">
                <Star className="h-3 w-3" />
                <span>{achievement.achievement.reward_xp} XP</span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function AchievementGrid() {
  const [achievements, setAchievements] = useState<UserAchievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [refreshing, setRefreshing] = useState(false);

  const fetchAchievements = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await gamificationApi.getAchievements();
      setAchievements(data);
    } catch (err) {
      console.error('Error fetching achievements:', err);
      setError(err instanceof Error ? err.message : 'Failed to load achievements');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      const data = await gamificationApi.getAchievements();
      setAchievements(data);
    } catch (err) {
      console.error('Error refreshing achievements:', err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAchievements();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner />
        <span className="ml-2">Loading achievements...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="p-6">
          <div className="flex items-center space-x-2 text-red-600">
            <Award className="h-5 w-5" />
            <span className="font-medium">Error loading achievements</span>
          </div>
          <p className="text-red-600 text-sm mt-2">{error}</p>
        </CardContent>
      </Card>
    );
  }

  const categories = [
    { id: 'all', name: 'All Achievements', icon: Award },
    { id: 'expense_tracking', name: 'Expense Tracking', icon: Target },
    { id: 'invoice_management', name: 'Invoice Management', icon: TrendingUp },
    { id: 'habit_formation', name: 'Habit Formation', icon: Star },
    { id: 'financial_health', name: 'Financial Health', icon: Trophy },
    { id: 'exploration', name: 'Exploration', icon: Award }
  ];

  const filteredAchievements = selectedCategory === 'all' 
    ? achievements 
    : achievements.filter(a => a.achievement.category === selectedCategory);

  const completedCount = filteredAchievements.filter(a => a.is_completed).length;
  const totalCount = filteredAchievements.length;

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Award className="h-5 w-5 text-purple-500" />
              <span>Achievements</span>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className="text-sm">
                {completedCount} / {totalCount} Completed
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
                className="h-8 w-8 p-0"
              >
                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Overall Progress</span>
              <span className="font-medium">{totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0}%</span>
            </div>
            <Progress value={totalCount > 0 ? (completedCount / totalCount) * 100 : 0} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Category Tabs */}
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
        <TabsList className="grid w-full grid-cols-3 lg:grid-cols-6">
          {categories.map((category) => {
            const IconComponent = category.icon;
            return (
              <TabsTrigger key={category.id} value={category.id} className="text-xs">
                <IconComponent className="h-4 w-4 mr-1" />
                <span className="hidden sm:inline">{category.name}</span>
              </TabsTrigger>
            );
          })}
        </TabsList>

        {categories.map((category) => (
          <TabsContent key={category.id} value={category.id}>
            {filteredAchievements.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredAchievements.map((achievement) => (
                  <AchievementCard key={achievement.id} achievement={achievement} />
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="p-8 text-center">
                  <Lock className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Achievements Yet</h3>
                  <p className="text-gray-600">
                    Start using the app to unlock achievements in this category!
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}