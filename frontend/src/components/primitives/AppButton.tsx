import * as React from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type AppButtonVariant =
  | "primary"
  | "secondary"
  | "outline"
  | "ghost"
  | "link"
  | "destructive";

type AppButtonSize = "sm" | "md" | "lg" | "icon";

export type AppButtonProps = Omit<
  React.ComponentProps<typeof Button>,
  "variant" | "size"
> & {
  variant?: AppButtonVariant;
  size?: AppButtonSize;
  loading?: boolean;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
};

const variantMap: Record<AppButtonVariant, React.ComponentProps<typeof Button>["variant"]> =
  {
    primary: "default",
    secondary: "secondary",
    outline: "outline",
    ghost: "ghost",
    link: "link",
    destructive: "destructive",
  };

const sizeMap: Record<AppButtonSize, React.ComponentProps<typeof Button>["size"]> =
  {
    sm: "sm",
    md: "default",
    lg: "lg",
    icon: "icon",
  };

export function AppButton({
  variant = "primary",
  size = "md",
  loading = false,
  startIcon,
  endIcon,
  className,
  disabled,
  children,
  ...props
}: AppButtonProps) {
  return (
    <Button
      variant={variantMap[variant]}
      size={sizeMap[size]}
      disabled={disabled || loading}
      aria-busy={loading}
      className={cn(loading && "opacity-80", className)}
      {...props}
    >
      {startIcon ? <span className="inline-flex items-center">{startIcon}</span> : null}
      {loading ? "Loading..." : children}
      {endIcon ? <span className="inline-flex items-center">{endIcon}</span> : null}
    </Button>
  );
}
