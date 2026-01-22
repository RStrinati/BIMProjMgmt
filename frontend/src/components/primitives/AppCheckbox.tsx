import * as React from "react";

import { cn } from "@/lib/utils";

type AppCheckboxProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  helperText?: string;
  error?: string;
  containerClassName?: string;
};

export function AppCheckbox({
  label,
  helperText,
  error,
  containerClassName,
  className,
  id,
  ...props
}: AppCheckboxProps) {
  const checkboxId = id ?? React.useId();

  return (
    <div className={cn("grid gap-1", containerClassName)}>
      <label className="inline-flex items-center gap-2 text-sm" htmlFor={checkboxId}>
        <input
          id={checkboxId}
          type="checkbox"
          className={cn(
            "h-4 w-4 rounded border border-input text-primary shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
            error && "border-destructive focus-visible:ring-destructive",
            className
          )}
          {...props}
        />
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
