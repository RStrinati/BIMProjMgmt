import * as React from "react";
import { CheckCircle2, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { DashboardBlock } from "./DashboardBlock";
import { SettingsBlock } from "./SettingsBlock";

type CheckItem = {
  id: string;
  label: string;
  checked: boolean;
};

const initialChecks: CheckItem[] = [
  { id: "bg-card", label: "bg-card surfaces visible", checked: false },
  { id: "text-muted", label: "text-muted-foreground appears muted", checked: false },
  { id: "border", label: "border-border visible", checked: false },
  { id: "spacing", label: "spacing (gap/padding) is applied", checked: false },
  { id: "radius", label: "rounded corners visible", checked: false },
];

type BlockErrorBoundaryProps = {
  name: string;
  children: React.ReactNode;
};

type BlockErrorBoundaryState = {
  error?: Error;
};

class BlockErrorBoundary extends React.Component<
  BlockErrorBoundaryProps,
  BlockErrorBoundaryState
> {
  state: BlockErrorBoundaryState = {};

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    const { error } = this.state;
    if (error) {
      return (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-sm text-destructive">
          <div className="font-semibold">Block failed to render: {this.props.name}</div>
          <div className="mt-2 whitespace-pre-wrap">{error.message}</div>
        </div>
      );
    }

    return this.props.children;
  }
}

export function ShadcnBlocksSection() {
  const [checks, setChecks] = React.useState<CheckItem[]>(initialChecks);

  const toggleCheck = (id: string) => {
    setChecks((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, checked: !item.checked } : item
      )
    );
  };

  return (
    <div className="rounded-xl border border-border bg-background text-foreground">
      <div className="border-b border-border px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-lg font-semibold">Shadcn Blocks</div>
            <div className="text-sm text-muted-foreground">
              Reference blocks rendered with Tailwind + shadcn tokens.
            </div>
          </div>
          <Badge variant="secondary">Playground only</Badge>
        </div>
      </div>

      <div className="min-h-[600px] space-y-8 p-6">
        <div className="space-y-4">
          <div className="text-sm font-semibold">Tailwind Compile Test</div>
          <div className="p-6">
            <div className="rounded-xl bg-black p-6 text-white">
              Tailwind compile test — this must be black with white text.
            </div>
          </div>
          <div className="text-sm font-semibold">Token Test</div>
          <div className="rounded-xl border bg-card p-6 text-foreground">
            <div className="text-lg font-semibold">Token test</div>
            <div className="text-sm text-muted-foreground">
              This text must look muted.
            </div>
          </div>
        </div>

        <Separator />

        <div className="space-y-4">
          <div className="text-sm font-semibold">Dashboard Block</div>
          <div className="bg-background text-foreground p-6">
            <BlockErrorBoundary name="DashboardBlock">
              <DashboardBlock />
            </BlockErrorBoundary>
          </div>
        </div>

        <Separator />

        <div className="space-y-4">
          <div className="text-sm font-semibold">Settings / Form Block</div>
          <div className="bg-background text-foreground p-6">
            <BlockErrorBoundary name="SettingsBlock">
              <SettingsBlock />
            </BlockErrorBoundary>
          </div>
        </div>

        <Separator />

        <div className="space-y-3">
          <div className="text-sm font-semibold">Reference Parity Checks</div>
          <div className="grid gap-2 md:grid-cols-2">
            {checks.map((item) => (
              <label
                key={item.id}
                className="flex cursor-pointer items-center justify-between gap-3 rounded-lg border border-border bg-muted/40 px-3 py-2 text-sm"
              >
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-border"
                    checked={item.checked}
                    onChange={() => toggleCheck(item.id)}
                  />
                  <span>{item.label}</span>
                </div>
                {item.checked ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-muted-foreground" />
                )}
              </label>
            ))}
          </div>
          <div className="text-xs text-muted-foreground">
            Use this checklist for manual visual confirmation only.
          </div>
        </div>
      </div>
    </div>
  );
}
