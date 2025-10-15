import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Loader2, FileText, Users, Package, CheckCircle, Bell, Calendar, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { formatDate } from "@/lib/utils";
import { activityApi, ActivityItem } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface RecentActivityProps {
  refreshKey?: number;
}

export function RecentActivity({ refreshKey }: RecentActivityProps) {
  const { t } = useTranslation();
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);

  const getActivityIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'invoice':
        return <FileText className="h-4 w-4 text-blue-600" />;
      case 'client':
        return <Users className="h-4 w-4 text-green-600" />;
      case 'inventory':
        return <Package className="h-4 w-4 text-purple-600" />;
      case 'approval':
        return <CheckCircle className="h-4 w-4 text-orange-600" />;
      case 'reminder':
        return <Bell className="h-4 w-4 text-red-600" />;
      case 'expense':
        return <TrendingUp className="h-4 w-4 text-indigo-600" />;
      case 'report':
        return <Calendar className="h-4 w-4 text-teal-600" />;
      default:
        return <FileText className="h-4 w-4 text-gray-600" />;
    }
  };

  const getActivityBadge = (type: ActivityItem['type'], status?: string) => {
    if (status) {
      switch (status) {
        case 'paid':
        case 'approved':
        case 'completed':
          return <Badge className="text-xs bg-green-100 text-green-800">Completed</Badge>;
        case 'pending':
        case 'draft':
          return <Badge className="text-xs bg-yellow-100 text-yellow-800">Pending</Badge>;
        case 'overdue':
        case 'rejected':
          return <Badge className="text-xs bg-red-100 text-red-800">Attention</Badge>;
        default:
          return <Badge className="text-xs bg-gray-100 text-gray-800">{status}</Badge>;
      }
    }

    switch (type) {
      case 'invoice':
        return <Badge className="text-xs bg-blue-100 text-blue-800">Invoice</Badge>;
      case 'client':
        return <Badge className="text-xs bg-green-100 text-green-800">Client</Badge>;
      case 'inventory':
        return <Badge className="text-xs bg-purple-100 text-purple-800">Inventory</Badge>;
      case 'approval':
        return <Badge className="text-xs bg-orange-100 text-orange-800">Approval</Badge>;
      case 'reminder':
        return <Badge className="text-xs bg-red-100 text-red-800">Reminder</Badge>;
      case 'expense':
        return <Badge className="text-xs bg-indigo-100 text-indigo-800">Expense</Badge>;
      case 'report':
        return <Badge className="text-xs bg-teal-100 text-teal-800">Report</Badge>;
      default:
        return <Badge className="text-xs bg-gray-100 text-gray-800">Activity</Badge>;
    }
  };

  const fetchActivities = async () => {
    setLoading(true);
    try {
      const recentActivities = await activityApi.getRecentActivities(8);
      setActivities(recentActivities);
    } catch (error) {
      console.error("Failed to fetch recent activities:", error);
      toast.error("Failed to load recent activities");
      
      // Fallback to empty array on error
      setActivities([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActivities();
  }, [refreshKey]);

  const formatAmount = (amount?: number, currency?: string) => {
    if (!amount || !currency) return null;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  return (
    <Card className="border-l-4 border-l-secondary bg-gradient-to-br from-secondary/5 to-transparent hover:shadow-lg transition-all duration-300">
      <CardHeader className="pb-4">
        <CardTitle className="text-xl font-semibold flex items-center gap-2">
          <div className="p-2 rounded-lg bg-secondary/10">
            <Calendar className="h-5 w-5 text-secondary" />
          </div>
          Activity Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          {loading ? (
            <div className="flex justify-center items-center h-full">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : activities.length > 0 ? (
            <div className="h-full overflow-y-auto space-y-3 pr-2">
              {activities.map((activity) => (
            <div key={activity.id} className="flex items-start gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors">
              <div className="p-2 rounded-lg bg-muted/50 flex-shrink-0">
                {getActivityIcon(activity.type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="font-medium text-sm leading-tight">
                      {activity.link ? (
                        <Link to={activity.link} className="hover:underline">
                          {activity.title}
                        </Link>
                      ) : (
                        activity.title
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {activity.description}
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-muted-foreground">
                        {formatDate(activity.timestamp)}
                      </span>
                      {activity.amount && (
                        <span className="text-xs font-medium">
                          {formatAmount(activity.amount, activity.currency)}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    {getActivityBadge(activity.type, activity.status)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Calendar className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No recent activity</p>
              <p className="text-sm text-muted-foreground mt-1">
                Activity will appear here as you use the system
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}