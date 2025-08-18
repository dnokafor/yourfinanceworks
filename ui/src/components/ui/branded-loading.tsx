import { Building, Loader2 } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api';
import { cn } from '@/lib/utils';

interface BrandedLoadingProps {
  logoUrl?: string;
  companyName?: string;
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function BrandedLoading({ 
  logoUrl, 
  companyName = 'InvoiceApp', 
  message = 'Loading...',
  size = 'md',
  className 
}: BrandedLoadingProps) {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16'
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  return (
    <div className={cn(
      "flex flex-col items-center justify-center space-y-4 p-8",
      className
    )}>
      <div className="relative">
        {logoUrl ? (
          <div className="relative">
            <img 
              src={`${API_BASE_URL}${logoUrl}`}
              alt={`${companyName} Logo`}
              className={cn("object-contain rounded animate-pulse", sizeClasses[size])}
              onError={(e) => {
                console.error('Failed to load logo in loading screen:', e);
                e.currentTarget.style.display = 'none';
              }}
            />
            <Loader2 className={cn(
              "absolute inset-0 animate-spin text-primary/60",
              sizeClasses[size]
            )} />
          </div>
        ) : (
          <div className="relative">
            <div className={cn(
              "bg-primary rounded flex items-center justify-center animate-pulse",
              sizeClasses[size]
            )}>
              <Building className={cn(
                "text-primary-foreground",
                size === 'sm' ? 'h-4 w-4' : size === 'md' ? 'h-6 w-6' : 'h-8 w-8'
              )} />
            </div>
            <Loader2 className={cn(
              "absolute inset-0 animate-spin text-primary/60",
              sizeClasses[size]
            )} />
          </div>
        )}
      </div>
      
      <div className="text-center space-y-2">
        <h3 className={cn(
          "font-semibold text-foreground",
          textSizeClasses[size]
        )}>
          {companyName}
        </h3>
        <p className={cn(
          "text-muted-foreground",
          size === 'sm' ? 'text-xs' : size === 'md' ? 'text-sm' : 'text-base'
        )}>
          {message}
        </p>
      </div>
    </div>
  );
}