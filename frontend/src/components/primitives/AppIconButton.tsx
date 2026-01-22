import * as React from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type AppIconButtonProps = Omit<
  React.ComponentProps<typeof Button>,
  "size" | "variant"
> & {
  label: string;
  variant?: "primary" | "secondary" | "outline" | "ghost" | "destructive";
};

const variantMap: Record<
  NonNullable<AppIconButtonProps["variant"]>,
  React.ComponentProps<typeof Button>["variant"]
> = {
  primary: "default",
  secondary: "secondary",
  outline: "outline",
  ghost: "ghost",
  destructive: "destructive",
};

export function AppIconButton({
  label,
  variant = "ghost",
  className,
  ...props
}: AppIconButtonProps) {
  return (
    <Button
      type="button"
      size="icon"
      variant={variantMap[variant]}
      aria-label={label}
      className={cn(className)}
      {...props}
    />
  );
}
