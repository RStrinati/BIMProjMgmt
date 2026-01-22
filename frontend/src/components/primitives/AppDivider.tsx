import * as React from "react";

import { cn } from "@/lib/utils";

type AppDividerProps = React.HTMLAttributes<HTMLDivElement>;

export function AppDivider({ className, ...props }: AppDividerProps) {
  return <div className={cn("h-px w-full bg-border", className)} {...props} />;
}
