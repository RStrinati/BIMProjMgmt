import * as React from "react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type AppCardDensity = "comfortable" | "compact";

type AppCardProps = React.HTMLAttributes<HTMLDivElement> & {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  footer?: React.ReactNode;
  density?: AppCardDensity;
};

export function AppCard({
  title,
  subtitle,
  actions,
  footer,
  density = "comfortable",
  className,
  children,
  ...props
}: AppCardProps) {
  const paddingClass = density === "compact" ? "p-4" : "p-6";
  const hasHeader = Boolean(title || subtitle || actions);

  return (
    <Card className={cn("overflow-hidden", className)} {...props}>
      {hasHeader ? (
        <div className={cn("flex items-start justify-between gap-4", paddingClass)}>
          <div className="space-y-1">
            {title ? <div className="text-sm font-semibold">{title}</div> : null}
            {subtitle ? (
              <div className="text-xs text-muted-foreground">{subtitle}</div>
            ) : null}
          </div>
          {actions ? <div className="shrink-0">{actions}</div> : null}
        </div>
      ) : null}
      {children ? (
        <div className={cn(paddingClass, hasHeader && "pt-0")}>{children}</div>
      ) : null}
      {footer ? (
        <div className={cn("border-t border-border", paddingClass)}>{footer}</div>
      ) : null}
    </Card>
  );
}
