import * as React from "react";

import { Badge, BadgeProps } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type AppStatus =
  | "Draft"
  | "Active"
  | "Blocked"
  | "Done"
  | "Overdue"
  | "On Hold";

type AppBadgeProps = BadgeProps & {
  status?: AppStatus;
};

const statusMap: Record<AppStatus, { variant: BadgeProps["variant"]; className?: string }> =
  {
    Draft: { variant: "secondary", className: "text-muted-foreground" },
    Active: { variant: "default" },
    Blocked: { variant: "destructive" },
    Done: {
      variant: "outline",
      className: "border-emerald-500/40 text-emerald-600 bg-emerald-50",
    },
    Overdue: { variant: "destructive" },
    "On Hold": {
      variant: "secondary",
      className: "text-muted-foreground border border-dashed border-muted-foreground/40",
    },
  };

export function AppBadge({ status, className, variant, children, ...props }: AppBadgeProps) {
  if (status) {
    const mapped = statusMap[status];
    return (
      <Badge
        variant={mapped.variant}
        className={cn(mapped.className, className)}
        {...props}
      >
        {children ?? status}
      </Badge>
    );
  }

  return (
    <Badge variant={variant} className={className} {...props}>
      {children}
    </Badge>
  );
}
