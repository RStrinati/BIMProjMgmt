import * as React from "react";

import { cn } from "@/lib/utils";

type AppSwitchProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  helperText?: string;
  error?: string;
  containerClassName?: string;
};

export function AppSwitch({
  label,
  helperText,
  error,
  containerClassName,
  className,
  id,
  ...props
}: AppSwitchProps) {
  const switchId = id ?? React.useId();

  return (
    <div className={cn("grid gap-1", containerClassName)}>
      <label className="inline-flex items-center gap-2 text-sm" htmlFor={switchId}>
        <span className="relative inline-flex h-5 w-9 items-center">
          <input
            id={switchId}
            type="checkbox"
            role="switch"
            className={cn("peer sr-only", className)}
            {...props}
          />
          <span
            className={cn(
              "absolute inset-0 rounded-full border border-transparent bg-muted transition-colors",
              "peer-checked:bg-primary peer-focus-visible:ring-2 peer-focus-visible:ring-ring",
              error && "border-destructive peer-focus-visible:ring-destructive"
            )}
          />
          <span className="absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-background shadow transition-transform peer-checked:translate-x-4" />
        </span>
        {label ? <span className="text-sm">{label}</span> : null}
      </label>
      {helperText || error ? (
        <p className={cn("text-xs", error ? "text-destructive" : "text-muted-foreground")}>
          {error ?? helperText}
        </p>
      ) : null}
    </div>
  );
}
