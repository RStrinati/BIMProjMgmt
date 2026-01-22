import * as React from "react";

import { cn } from "@/lib/utils";

type AppSelectProps = React.SelectHTMLAttributes<HTMLSelectElement> & {
  label?: string;
  helperText?: string;
  error?: string;
  placeholder?: string;
  containerClassName?: string;
};

export function AppSelect({
  label,
  helperText,
  error,
  placeholder,
  containerClassName,
  className,
  id,
  children,
  ...props
}: AppSelectProps) {
  const selectId = id ?? React.useId();

  return (
    <div className={cn("grid gap-1", containerClassName)}>
      {label ? (
        <label className="text-sm font-medium" htmlFor={selectId}>
          {label}
        </label>
      ) : null}
      <select
        id={selectId}
        className={cn(
          "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
          error && "border-destructive focus-visible:ring-destructive",
          className
        )}
        {...props}
      >
        {placeholder ? (
          <option value="" disabled>
            {placeholder}
          </option>
        ) : null}
        {children}
      </select>
      {helperText || error ? (
        <p className={cn("text-xs", error ? "text-destructive" : "text-muted-foreground")}>
          {error ?? helperText}
        </p>
      ) : null}
    </div>
  );
}
