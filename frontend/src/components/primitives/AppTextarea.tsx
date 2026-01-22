import * as React from "react";

import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

type AppTextareaProps = React.ComponentProps<typeof Textarea> & {
  label?: string;
  helperText?: string;
  error?: string;
  containerClassName?: string;
};

export function AppTextarea({
  label,
  helperText,
  error,
  containerClassName,
  className,
  id,
  ...props
}: AppTextareaProps) {
  const textareaId = id ?? React.useId();

  return (
    <div className={cn("grid gap-1", containerClassName)}>
      {label ? (
        <label className="text-sm font-medium" htmlFor={textareaId}>
          {label}
        </label>
      ) : null}
      <Textarea
        id={textareaId}
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
