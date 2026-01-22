import * as React from "react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type AppInputProps = React.ComponentProps<typeof Input> & {
  label?: string;
  helperText?: string;
  error?: string;
  containerClassName?: string;
};

export function AppInput({
  label,
  helperText,
  error,
  containerClassName,
  className,
  id,
  ...props
}: AppInputProps) {
  const inputId = id ?? React.useId();

  return (
    <div className={cn("grid gap-1", containerClassName)}>
      {label ? (
        <label className="text-sm font-medium" htmlFor={inputId}>
          {label}
        </label>
      ) : null}
      <Input
        id={inputId}
        className={cn(error && "border-destructive focus-visible:ring-destructive", className)}
        {...props}
      />
      {helperText || error ? (
        <p className={cn("text-xs", error ? "text-destructive" : "text-muted-foreground")}>
          {error ?? helperText}
        </p>
      ) : null}
    </div>
  );
}
