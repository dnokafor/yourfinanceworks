import * as React from "react";
import { cn } from "@/lib/utils";

// Display Typography Components
export const DisplayXL = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h1
    ref={ref}
    className={cn("text-display-xl font-bold text-foreground", className)}
    {...props}
  />
));
DisplayXL.displayName = "DisplayXL";

export const DisplayLG = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h1
    ref={ref}
    className={cn("text-display-lg font-bold text-foreground", className)}
    {...props}
  />
));
DisplayLG.displayName = "DisplayLG";

export const DisplayMD = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h1
    ref={ref}
    className={cn("text-display-md font-bold text-foreground", className)}
    {...props}
  />
));
DisplayMD.displayName = "DisplayMD";

export const DisplaySM = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h2
    ref={ref}
    className={cn("text-display-sm font-semibold text-foreground", className)}
    {...props}
  />
));
DisplaySM.displayName = "DisplaySM";

// Heading Typography Components
export const HeadingXL = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h2
    ref={ref}
    className={cn("text-heading-xl font-semibold text-foreground", className)}
    {...props}
  />
));
HeadingXL.displayName = "HeadingXL";

export const HeadingLG = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn("text-heading-lg font-semibold text-foreground", className)}
    {...props}
  />
));
HeadingLG.displayName = "HeadingLG";

export const HeadingMD = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h4
    ref={ref}
    className={cn("text-heading-md font-medium text-foreground", className)}
    {...props}
  />
));
HeadingMD.displayName = "HeadingMD";

export const HeadingSM = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn("text-heading-sm font-medium text-foreground", className)}
    {...props}
  />
));
HeadingSM.displayName = "HeadingSM";

// Body Typography Components
export const BodyXL = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-body-xl text-foreground", className)}
    {...props}
  />
));
BodyXL.displayName = "BodyXL";

export const BodyLG = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-body-lg text-foreground", className)}
    {...props}
  />
));
BodyLG.displayName = "BodyLG";

export const BodyMD = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-body-md text-foreground", className)}
    {...props}
  />
));
BodyMD.displayName = "BodyMD";

export const BodySM = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-body-sm text-muted-foreground", className)}
    {...props}
  />
));
BodySM.displayName = "BodySM";

// Caption Typography Component
export const Caption = React.forwardRef<
  HTMLSpanElement,
  React.HTMLAttributes<HTMLSpanElement>
>(({ className, ...props }, ref) => (
  <span
    ref={ref}
    className={cn("text-caption text-muted-foreground font-medium uppercase", className)}
    {...props}
  />
));
Caption.displayName = "Caption";

// Financial Typography Components
export const CurrencyDisplay = React.forwardRef<
  HTMLSpanElement,
  React.HTMLAttributes<HTMLSpanElement> & {
    variant?: 'default' | 'success' | 'warning' | 'destructive';
    size?: 'sm' | 'md' | 'lg' | 'xl';
  }
>(({ className, variant = 'default', size = 'md', ...props }, ref) => {
  const variantClasses = {
    default: 'text-foreground',
    success: 'text-success',
    warning: 'text-warning',
    destructive: 'text-destructive',
  };

  const sizeClasses = {
    sm: 'text-sm font-medium',
    md: 'text-lg font-semibold',
    lg: 'text-2xl font-bold',
    xl: 'text-3xl font-bold',
  };

  return (
    <span
      ref={ref}
      className={cn(
        "tabular-nums tracking-tight",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    />
  );
});
CurrencyDisplay.displayName = "CurrencyDisplay";

// Status Badge Typography
export const StatusText = React.forwardRef<
  HTMLSpanElement,
  React.HTMLAttributes<HTMLSpanElement> & {
    status: 'paid' | 'pending' | 'overdue' | 'partially-paid';
  }
>(({ className, status, ...props }, ref) => {
  const statusClasses = {
    paid: 'status-paid',
    pending: 'status-pending',
    overdue: 'status-overdue',
    'partially-paid': 'status-partially-paid',
  };

  return (
    <span
      ref={ref}
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
        statusClasses[status],
        className
      )}
      {...props}
    />
  );
});
StatusText.displayName = "StatusText";