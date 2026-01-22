import * as React from "react";
import {
  Box,
  Button as MuiButton,
  Card as MuiCard,
  CardContent as MuiCardContent,
  CardHeader as MuiCardHeader,
  Checkbox as MuiCheckbox,
  Chip,
  Divider as MuiDivider,
  FormControl,
  IconButton as MuiIconButton,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  Switch as MuiSwitch,
  TextField,
  Typography,
} from "@mui/material";

import { AppBadge, AppStatus } from "@/components/primitives/AppBadge";
import { AppButton } from "@/components/primitives/AppButton";
import { AppCard } from "@/components/primitives/AppCard";
import { AppCheckbox } from "@/components/primitives/AppCheckbox";
import { AppDivider } from "@/components/primitives/AppDivider";
import { AppIconButton } from "@/components/primitives/AppIconButton";
import { AppInput } from "@/components/primitives/AppInput";
import { AppSelect } from "@/components/primitives/AppSelect";
import { AppSwitch } from "@/components/primitives/AppSwitch";
import { AppTextarea } from "@/components/primitives/AppTextarea";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { LinearListRow } from "@/components/ui/LinearList";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { ShadcnBlocksSection } from "@/pages/ui-playground/blocks/ShadcnBlocksSection";

type Density = "comfortable" | "compact";
type Mode = "shadcn" | "mui" | "wrapper";

type WorkspaceRow = {
  id: string;
  title: string;
  subtitle: string;
  status: AppStatus;
  progress: number;
  chips: string[];
  owner: string;
  due: string;
  budget: string;
  billed: string;
  notes: string;
};

const STATUS_OPTIONS: AppStatus[] = [
  "Draft",
  "Active",
  "Blocked",
  "Done",
  "Overdue",
  "On Hold",
];

const WORKSPACE_ROWS: WorkspaceRow[] = [
  {
    id: "SVC-001",
    title: "Architecture - Concept",
    subtitle: "Stage 2, Area plans",
    status: "Active",
    progress: 62,
    chips: ["LOD 200", "3 reviews"],
    owner: "Ava",
    due: "Mar 18",
    budget: "$120k",
    billed: "$66k",
    notes: "Awaiting client confirmation on lobby layout revisions.",
  },
  {
    id: "SVC-002",
    title: "Structure - Core",
    subtitle: "Stage 3, Coordination",
    status: "Blocked",
    progress: 28,
    chips: ["LOD 300", "2 issues"],
    owner: "Ravi",
    due: "Mar 24",
    budget: "$88k",
    billed: "$21k",
    notes: "Resolve penetrations with mechanical before issuing package.",
  },
  {
    id: "SVC-003",
    title: "MEP - Services",
    subtitle: "Stage 3, Clash set",
    status: "On Hold",
    progress: 40,
    chips: ["LOD 300", "Hold for BIM"],
    owner: "Nora",
    due: "Apr 02",
    budget: "$96k",
    billed: "$38k",
    notes: "Paused pending updated MEP load schedules.",
  },
  {
    id: "SVC-004",
    title: "Facade - Package",
    subtitle: "Stage 4, Tender",
    status: "Overdue",
    progress: 78,
    chips: ["Tender", "5 RFIs"],
    owner: "Tomas",
    due: "Feb 28",
    budget: "$110k",
    billed: "$92k",
    notes: "Overdue: align glazing spec with updated supplier list.",
  },
  {
    id: "SVC-005",
    title: "Interior - Fitout",
    subtitle: "Stage 2, Fixtures",
    status: "Draft",
    progress: 12,
    chips: ["Draft scope", "No reviews"],
    owner: "Lea",
    due: "Apr 10",
    budget: "$52k",
    billed: "$0",
    notes: "Drafting scope and preliminary mood boards.",
  },
  {
    id: "SVC-006",
    title: "Landscape - Plaza",
    subtitle: "Stage 3, External",
    status: "Active",
    progress: 55,
    chips: ["LOD 250", "2 reviews"],
    owner: "Kenji",
    due: "Mar 30",
    budget: "$60k",
    billed: "$33k",
    notes: "Coordinate planting schedule with civil drainage.",
  },
  {
    id: "SVC-007",
    title: "Vertical Transport",
    subtitle: "Stage 4, IFC",
    status: "Done",
    progress: 100,
    chips: ["IFC issued", "0 issues"],
    owner: "Maya",
    due: "Feb 20",
    budget: "$44k",
    billed: "$44k",
    notes: "Package issued and signed off.",
  },
  {
    id: "SVC-008",
    title: "Fire Engineering",
    subtitle: "Stage 3, Peer review",
    status: "Active",
    progress: 47,
    chips: ["Peer review", "2 actions"],
    owner: "Omar",
    due: "Apr 06",
    budget: "$70k",
    billed: "$29k",
    notes: "Awaiting peer feedback to close outstanding actions.",
  },
];
function StatusPill({ status, mode }: { status: AppStatus; mode: Mode }) {
  if (mode === "mui") {
    const colorMap: Record<AppStatus, "default" | "success" | "warning" | "error" | "info"> =
      {
        Draft: "default",
        Active: "info",
        Blocked: "error",
        Done: "success",
        Overdue: "error",
        "On Hold": "warning",
      };
    return <Chip label={status} color={colorMap[status]} size="small" variant="outlined" />;
  }
  if (mode === "wrapper") {
    return <AppBadge status={status} />;
  }
  const badgeStyles: Record<AppStatus, { variant: "default" | "secondary" | "destructive" | "outline"; className?: string }> =
    {
      Draft: { variant: "secondary", className: "text-muted-foreground" },
      Active: { variant: "default" },
      Blocked: { variant: "destructive" },
      Done: { variant: "outline", className: "border-emerald-500/40 text-emerald-600 bg-emerald-50" },
      Overdue: { variant: "destructive" },
      "On Hold": {
        variant: "secondary",
        className: "text-muted-foreground border border-dashed border-muted-foreground/40",
      },
    };
  const style = badgeStyles[status];
  return (
    <Badge variant={style.variant} className={style.className}>
      {status}
    </Badge>
  );
}

function FieldBlock({
  label,
  helperText,
  error,
  htmlFor,
  children,
}: {
  label: string;
  helperText?: string;
  error?: string;
  htmlFor?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid gap-1">
      <label className="text-sm font-medium" htmlFor={htmlFor}>
        {label}
      </label>
      {children}
      {helperText || error ? (
        <p className={cn("text-xs", error ? "text-destructive" : "text-muted-foreground")}>
          {error ?? helperText}
        </p>
      ) : null}
    </div>
  );
}

function RightPanelSection({
  title,
  action,
  children,
  density,
  defaultOpen = true,
}: {
  title: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  density: Density;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = React.useState(defaultOpen);
  const padding = density === "compact" ? "px-4 py-2" : "px-5 py-3";
  const bodyPadding = density === "compact" ? "px-4 pb-3 pt-2" : "px-5 pb-4 pt-3";

  return (
    <div className="rounded-lg border border-border bg-background shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className={cn("flex w-full items-center justify-between text-left", padding)}
        aria-expanded={open}
      >
        <span className="text-sm font-semibold">{title}</span>
        <span className="flex items-center gap-2 text-xs text-muted-foreground">
          {action}
          <span>{open ? "Hide" : "Show"}</span>
        </span>
      </button>
      {open ? <div className={bodyPadding}>{children}</div> : null}
    </div>
  );
}

function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-border bg-muted/30 p-6 text-center">
      <div className="text-sm font-semibold">{title}</div>
      <div className="text-xs text-muted-foreground">{description}</div>
      {action ? <div className="pt-2">{action}</div> : null}
    </div>
  );
}

function InlineEditableCell({
  mode,
  type,
  value,
  options,
  dirty,
  onChange,
}: {
  mode: Mode;
  type: "text" | "select" | "toggle";
  value: string | boolean;
  options?: string[];
  dirty?: boolean;
  onChange: (value: string | boolean) => void;
}) {
  const indicator = dirty ? <span className="ml-2 h-2 w-2 rounded-full bg-amber-500" /> : null;

  if (type === "toggle") {
    if (mode === "mui") {
      return (
        <div className="flex items-center">
          <MuiSwitch
            checked={Boolean(value)}
            onChange={(event) => onChange(event.target.checked)}
          />
          {indicator}
        </div>
      );
    }

    if (mode === "wrapper") {
      return (
        <div className="flex items-center">
          <AppSwitch checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} />
          {indicator}
        </div>
      );
    }

    return (
      <div className="flex items-center">
        <AppSwitch checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} />
        {indicator}
      </div>
    );
  }

  if (type === "select") {
    const valueText = String(value ?? "");
    if (mode === "mui") {
      return (
        <div className="flex items-center gap-2">
          <FormControl size="small">
            <Select value={valueText} onChange={(event) => onChange(event.target.value)}>
              {options?.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {indicator}
        </div>
      );
    }
    if (mode === "wrapper") {
      return (
        <div className="flex items-center gap-2">
          <AppSelect value={valueText} onChange={(event) => onChange(event.target.value)}>
            {options?.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </AppSelect>
          {indicator}
        </div>
      );
    }
    return (
      <div className="flex items-center gap-2">
        <AppSelect value={valueText} onChange={(event) => onChange(event.target.value)}>
          {options?.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </AppSelect>
        {indicator}
      </div>
    );
  }

  const textValue = String(value ?? "");
  if (mode === "mui") {
    return (
      <div className="flex items-center gap-2">
        <TextField
          size="small"
          value={textValue}
          onChange={(event) => onChange(event.target.value)}
        />
        {indicator}
      </div>
    );
  }
  if (mode === "wrapper") {
    return (
      <div className="flex items-center gap-2">
        <AppInput value={textValue} onChange={(event) => onChange(event.target.value)} />
        {indicator}
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2">
      <Input value={textValue} onChange={(event) => onChange(event.target.value)} />
      {indicator}
    </div>
  );
}

function PanelCard({
  mode,
  density,
  title,
  subtitle,
  actions,
  children,
}: {
  mode: Mode;
  density: Density;
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  const paddingClass = density === "compact" ? "p-4" : "p-6";
  const muiPadding = density === "compact" ? 2 : 3;

  if (mode === "mui") {
    return (
      <MuiCard variant="outlined">
        <MuiCardHeader
          title={title}
          subheader={subtitle}
          action={actions}
          sx={{ px: muiPadding, pt: muiPadding, pb: 1 }}
        />
        <MuiCardContent sx={{ px: muiPadding, pt: 1, pb: muiPadding }}>
          {children}
        </MuiCardContent>
      </MuiCard>
    );
  }

  if (mode === "wrapper") {
    return (
      <AppCard title={title} subtitle={subtitle} density={density} actions={actions}>
        {children}
      </AppCard>
    );
  }

  return (
    <Card>
      <CardHeader className={paddingClass}>
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <CardTitle>{title}</CardTitle>
            {subtitle ? <CardDescription>{subtitle}</CardDescription> : null}
          </div>
          {actions ? <div className="shrink-0">{actions}</div> : null}
        </div>
      </CardHeader>
      <CardContent className={cn(paddingClass, "pt-0")}>{children}</CardContent>
    </Card>
  );
}
export default function UiPlaygroundPage() {
  const [density, setDensity] = React.useState<Density>("comfortable");
  const [mode, setMode] = React.useState<Mode>("shadcn");
  const [selectedRowId, setSelectedRowId] = React.useState<string>("SVC-001");
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editableLabel, setEditableLabel] = React.useState("Concept Set");
  const [editableStatus, setEditableStatus] = React.useState("Active");
  const [editableToggle, setEditableToggle] = React.useState(true);

  const [workspaceRows, setWorkspaceRows] = React.useState(() =>
    WORKSPACE_ROWS.map((row) => ({
      ...row,
      editableStatus: row.status,
      editableDirty: false,
    }))
  );

  const densityConfig = {
    rowPaddingY: density === "compact" ? 0.5 : 1.2,
    cardPadding: density === "compact" ? "p-4" : "p-6",
    metaTextClass: density === "compact" ? "text-xs" : "text-sm",
    kpiPadding: density === "compact" ? "p-4" : "p-5",
  };
  const muiCardPadding = density === "compact" ? 2 : 3;

  const selectedRow = React.useMemo(
    () => workspaceRows.find((row) => row.id === selectedRowId) ?? workspaceRows[0],
    [workspaceRows, selectedRowId]
  );

  const updateWorkspaceStatus = (id: string, status: AppStatus) => {
    setWorkspaceRows((prev) =>
      prev.map((row) =>
        row.id === id
          ? {
              ...row,
              editableStatus: status,
              editableDirty: row.status !== status,
            }
          : row
      )
    );
  };

  const topControls = (
    <div className="flex flex-wrap items-center gap-3">
      <div className="rounded-lg border border-border bg-background p-1 shadow-sm">
        <div className="flex items-center gap-1">
          {(["comfortable", "compact"] as Density[]).map((value) => (
            <Button
              key={value}
              variant={density === value ? "default" : "ghost"}
              size="sm"
              onClick={() => setDensity(value)}
            >
              {value === "comfortable" ? "Comfortable" : "Compact"}
            </Button>
          ))}
        </div>
      </div>
      <div className="rounded-lg border border-border bg-background p-1 shadow-sm">
        <div className="flex items-center gap-1">
          {(["shadcn", "mui", "wrapper"] as Mode[]).map((value) => (
            <Button
              key={value}
              variant={mode === value ? "default" : "ghost"}
              size="sm"
              onClick={() => setMode(value)}
            >
              {value === "shadcn" ? "Shadcn" : value === "mui" ? "MUI" : "Wrapper"}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <Box sx={{ p: 4 }}>
      <div className="space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <Typography variant="h4" sx={{ fontWeight: 600 }}>
              UI Playground
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Canonical UI patterns for Workspace tabs and gradual migration.
            </Typography>
          </div>
          {topControls}
        </div>

        <div className="grid gap-8 lg:grid-cols-[220px,1fr]">
          <nav className="space-y-2 lg:sticky lg:top-6 lg:self-start">
            {[
              { id: "tokens", label: "Tokens Preview" },
              { id: "shadcn-blocks", label: "Shadcn Blocks" },
              { id: "buttons", label: "Golden Primitives - Buttons" },
              { id: "inputs", label: "Golden Primitives - Inputs" },
              { id: "cards", label: "Golden Primitives - Cards" },
              { id: "linear-list", label: "Golden Patterns - LinearListRow" },
              { id: "right-panel", label: "Golden Patterns - RightPanel" },
              { id: "inline-edit", label: "Golden Patterns - InlineEditableCell" },
              { id: "overlays", label: "Overlays - Dialog and Menu" },
              { id: "kpi", label: "KPI - Strip and Cards" },
              { id: "workspace", label: "Workspace Mock" },
            ].map((section) => (
              <a
                key={section.id}
                href={`#${section.id}`}
                className="flex items-center justify-between rounded-md border border-transparent px-3 py-2 text-sm text-muted-foreground transition hover:border-border hover:bg-muted"
              >
                <span>{section.label}</span>
              </a>
            ))}
          </nav>

          <div className="space-y-10">
            <section id="tokens" className="space-y-4">
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Tokens Preview
              </Typography>
              <div className="grid gap-4 lg:grid-cols-2">
                <Card>
                  <CardHeader className={densityConfig.cardPadding}>
                    <CardTitle>Radius</CardTitle>
                    <CardDescription>Corner system for cards and panels.</CardDescription>
                  </CardHeader>
                  <CardContent className={densityConfig.cardPadding}>
                    <div className="grid grid-cols-4 gap-3">
                      {["rounded-sm", "rounded-md", "rounded-lg", "rounded-xl"].map(
                        (radius) => (
                          <div key={radius} className="space-y-2 text-center">
                            <div className={cn("h-12 w-full bg-muted", radius)} />
                            <div className="text-xs text-muted-foreground">{radius}</div>
                          </div>
                        )
                      )}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className={densityConfig.cardPadding}>
                    <CardTitle>Spacing</CardTitle>
                    <CardDescription>Primary spacing rhythm.</CardDescription>
                  </CardHeader>
                  <CardContent className={densityConfig.cardPadding}>
                    <div className="space-y-3">
                      {[1, 2, 3, 4].map((step) => (
                        <div key={step} className="flex items-center gap-3">
                          <div className="h-2 w-24 rounded-full bg-muted" />
                          <div className="text-xs text-muted-foreground">Step {step}</div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className={densityConfig.cardPadding}>
                    <CardTitle>Typography</CardTitle>
                    <CardDescription>Heading and metadata balance.</CardDescription>
                  </CardHeader>
                  <CardContent className={densityConfig.cardPadding}>
                    <div className="space-y-2">
                      <div className="text-xl font-semibold">Workspace Heading</div>
                      <div className="text-sm text-muted-foreground">
                        Section label and helper copy
                      </div>
                      <div className={cn(densityConfig.metaTextClass, "text-muted-foreground")}>
                        Meta line, timestamps, and list subtitles
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className={densityConfig.cardPadding}>
                    <CardTitle>Surfaces</CardTitle>
                    <CardDescription>Default, muted, and accent layers.</CardDescription>
                  </CardHeader>
                  <CardContent className={densityConfig.cardPadding}>
                    <div className="grid gap-3">
                      <div className="rounded-lg border border-border bg-background p-3 text-xs">
                        Surface: background
                      </div>
                      <div className="rounded-lg border border-border bg-muted/40 p-3 text-xs">
                        Surface: muted
                      </div>
                      <div className="rounded-lg border border-border bg-accent/30 p-3 text-xs">
                        Surface: accent
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </section>
            <section id="buttons" className="space-y-4">
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Golden Primitives - Buttons
              </Typography>
              <div className="rounded-lg border border-border bg-background p-4">
                <div className="flex flex-wrap gap-3">
                  {mode === "mui" ? (
                    <>
                      <MuiButton variant="contained">Primary</MuiButton>
                      <MuiButton variant="outlined">Secondary</MuiButton>
                      <MuiButton variant="text">Ghost</MuiButton>
                      <MuiButton variant="contained" color="error">
                        Destructive
                      </MuiButton>
                      <MuiButton disabled>Disabled</MuiButton>
                      <MuiButton variant="outlined">+ Icon Left</MuiButton>
                      <MuiIconButton size="small">...</MuiIconButton>
                    </>
                  ) : mode === "wrapper" ? (
                    <>
                      <AppButton variant="primary">Primary</AppButton>
                      <AppButton variant="secondary">Secondary</AppButton>
                      <AppButton variant="outline">Outline</AppButton>
                      <AppButton variant="ghost">Ghost</AppButton>
                      <AppButton variant="link">Link</AppButton>
                      <AppButton variant="destructive">Destructive</AppButton>
                      <AppButton loading>Loading</AppButton>
                      <AppButton variant="outline" startIcon={<span className="text-xs">+</span>}>
                        Icon Left
                      </AppButton>
                      <AppIconButton label="More actions">...</AppIconButton>
                    </>
                  ) : (
                    <>
                      <Button>Primary</Button>
                      <Button variant="secondary">Secondary</Button>
                      <Button variant="outline">Outline</Button>
                      <Button variant="ghost">Ghost</Button>
                      <Button variant="link">Link</Button>
                      <Button variant="destructive">Destructive</Button>
                      <Button disabled>Disabled</Button>
                      <Button variant="outline">
                        <span className="mr-2 text-xs">+</span>
                        Icon Left
                      </Button>
                      <Button size="icon" variant="ghost" aria-label="More actions">
                        ...
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </section>

            <section id="shadcn-blocks" className="space-y-4">
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Shadcn Blocks
              </Typography>
              <ShadcnBlocksSection />
            </section>

            <section id="inputs" className="space-y-4">
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Golden Primitives - Inputs, Select, Checkbox, Switch
              </Typography>
              <div className="grid gap-6 rounded-lg border border-border bg-background p-4 lg:grid-cols-2">
                <div className="space-y-4">
                  {mode === "mui" ? (
                    <>
                      <TextField label="Text input" placeholder="Enter service name" />
                      <TextField
                        label="Search input"
                        placeholder="Search services"
                        type="search"
                      />
                      <TextField label="Number input" type="number" defaultValue={24} />
                      <TextField
                        label="Error input"
                        error
                        helperText="Required field"
                        defaultValue="Missing"
                      />
                    </>
                  ) : mode === "wrapper" ? (
                    <>
                      <AppInput label="Text input" placeholder="Enter service name" />
                      <AppInput label="Search input" placeholder="Search services" type="search" />
                      <AppInput label="Number input" type="number" defaultValue={24} />
                      <AppInput
                        label="Error input"
                        defaultValue="Missing"
                        error="Required field"
                      />
                    </>
                  ) : (
                    <>
                      <FieldBlock label="Text input" htmlFor="text-input">
                        <Input id="text-input" placeholder="Enter service name" />
                      </FieldBlock>
                      <FieldBlock label="Search input" htmlFor="search-input">
                        <Input id="search-input" placeholder="Search services" type="search" />
                      </FieldBlock>
                      <FieldBlock label="Number input" htmlFor="number-input">
                        <Input id="number-input" type="number" defaultValue={24} />
                      </FieldBlock>
                      <FieldBlock label="Error input" htmlFor="error-input" error="Required field">
                        <Input
                          id="error-input"
                          defaultValue="Missing"
                          className="border-destructive focus-visible:ring-destructive"
                        />
                      </FieldBlock>
                    </>
                  )}
                </div>

                <div className="space-y-4">
                  {mode === "mui" ? (
                    <>
                      <FormControl fullWidth>
                        <InputLabel id="select-label">Service type</InputLabel>
                        <Select labelId="select-label" label="Service type" defaultValue="Design">
                          <MenuItem value="Design">Design</MenuItem>
                          <MenuItem value="Review">Review</MenuItem>
                          <MenuItem value="Survey">Survey</MenuItem>
                        </Select>
                      </FormControl>
                      <TextField
                        label="Textarea"
                        placeholder="Notes for the deliverable"
                        multiline
                        minRows={3}
                      />
                      <div className="flex items-center gap-3">
                        <MuiCheckbox defaultChecked />
                        <Typography variant="body2">Include in report</Typography>
                      </div>
                      <div className="flex items-center gap-3">
                        <MuiSwitch defaultChecked />
                        <Typography variant="body2">Auto notify client</Typography>
                      </div>
                    </>
                  ) : mode === "wrapper" ? (
                    <>
                      <AppSelect label="Service type" defaultValue="">
                        <option value="" disabled>
                          Choose type
                        </option>
                        <option value="Design">Design</option>
                        <option value="Review">Review</option>
                        <option value="Survey">Survey</option>
                      </AppSelect>
                      <AppTextarea label="Textarea" placeholder="Notes for the deliverable" />
                      <AppCheckbox label="Include in report" defaultChecked />
                      <AppSwitch label="Auto notify client" defaultChecked />
                    </>
                  ) : (
                    <>
                      <FieldBlock label="Service type" htmlFor="select-input">
                        <AppSelect id="select-input" defaultValue="">
                          <option value="" disabled>
                            Choose type
                          </option>
                          <option value="Design">Design</option>
                          <option value="Review">Review</option>
                          <option value="Survey">Survey</option>
                        </AppSelect>
                      </FieldBlock>
                      <FieldBlock label="Textarea" htmlFor="textarea-input">
                        <Textarea id="textarea-input" placeholder="Notes for the deliverable" />
                      </FieldBlock>
                      <AppCheckbox label="Include in report" defaultChecked />
                      <AppSwitch label="Auto notify client" defaultChecked />
                    </>
                  )}
                </div>
              </div>
            </section>

            <section id="cards" className="space-y-4">
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Golden Primitives - Cards, Badges, Dividers, Icon Buttons
              </Typography>
              <div className="grid gap-4 lg:grid-cols-3">
                {mode === "mui" ? (
                  <>
                    <MuiCard variant="outlined">
                      <MuiCardHeader
                        title="Service Summary"
                        subheader="Active services"
                        sx={{ px: muiCardPadding, pt: muiCardPadding, pb: 1 }}
                      />
                      <MuiCardContent sx={{ px: muiCardPadding, pt: 1, pb: muiCardPadding }}>
                        <Typography variant="body2" color="text.secondary">
                          12 services in progress, 3 blocked.
                        </Typography>
                      </MuiCardContent>
                    </MuiCard>
                    <MuiCard variant="outlined">
                      <MuiCardHeader
                        title="Status Map"
                        subheader="Standard labels"
                        sx={{ px: muiCardPadding, pt: muiCardPadding, pb: 1 }}
                      />
                      <MuiCardContent
                        className="flex flex-wrap gap-2"
                        sx={{ px: muiCardPadding, pt: 1, pb: muiCardPadding }}
                      >
                        {STATUS_OPTIONS.map((status) => (
                          <StatusPill key={status} status={status} mode={mode} />
                        ))}
                      </MuiCardContent>
                    </MuiCard>
                    <MuiCard variant="outlined">
                      <MuiCardHeader
                        title="Divider + Icon"
                        subheader="Panel actions"
                        sx={{ px: muiCardPadding, pt: muiCardPadding, pb: 1 }}
                      />
                      <MuiCardContent className="space-y-3" sx={{ px: muiCardPadding, pt: 1, pb: muiCardPadding }}>
                        <MuiDivider />
                        <MuiIconButton size="small">...</MuiIconButton>
                      </MuiCardContent>
                    </MuiCard>
                  </>
                ) : mode === "wrapper" ? (
                  <>
                    <AppCard
                      title="Service Summary"
                      subtitle="Active services"
                      density={density}
                    >
                      <div className="text-sm text-muted-foreground">
                        12 services in progress, 3 blocked.
                      </div>
                    </AppCard>
                    <AppCard title="Status Map" subtitle="Standard labels" density={density}>
                      <div className="flex flex-wrap gap-2">
                        {STATUS_OPTIONS.map((status) => (
                          <StatusPill key={status} status={status} mode={mode} />
                        ))}
                      </div>
                    </AppCard>
                    <AppCard title="Divider + Icon" subtitle="Panel actions" density={density}>
                      <div className="space-y-3">
                        <AppDivider />
                        <div>
                          <AppIconButton label="More actions">...</AppIconButton>
                        </div>
                      </div>
                    </AppCard>
                  </>
                ) : (
                  <>
                    <Card>
                      <CardHeader className={densityConfig.cardPadding}>
                        <CardTitle>Service Summary</CardTitle>
                        <CardDescription>Active services</CardDescription>
                      </CardHeader>
                      <CardContent className={densityConfig.cardPadding}>
                        <div className="text-sm text-muted-foreground">
                          12 services in progress, 3 blocked.
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className={densityConfig.cardPadding}>
                        <CardTitle>Status Map</CardTitle>
                        <CardDescription>Standard labels</CardDescription>
                      </CardHeader>
                      <CardContent className={densityConfig.cardPadding}>
                        <div className="flex flex-wrap gap-2">
                          {STATUS_OPTIONS.map((status) => (
                            <StatusPill key={status} status={status} mode={mode} />
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className={densityConfig.cardPadding}>
                        <CardTitle>Divider + Icon</CardTitle>
                        <CardDescription>Panel actions</CardDescription>
                      </CardHeader>
                      <CardContent className={densityConfig.cardPadding}>
                        <div className="space-y-3">
                          <div className="h-px bg-border" />
                          <Button size="icon" variant="ghost" aria-label="More actions">
                            ...
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </>
                )}
              </div>
            </section>

            <section id="linear-list" className="space-y-4">
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Golden Patterns - LinearListRow
              </Typography>
              <div className="rounded-lg border border-border bg-background">
                {WORKSPACE_ROWS.slice(0, 3).map((row) => {
                  const isSelected = row.id === selectedRowId;
                  return (
                    <LinearListRow
                      key={row.id}
                      columns={3}
                      onClick={() => setSelectedRowId(row.id)}
                      sx={{
                        py: densityConfig.rowPaddingY,
                        backgroundColor: isSelected ? "action.selected" : "background.paper",
                        borderLeft: isSelected ? "3px solid" : "3px solid transparent",
                        borderLeftColor: isSelected ? "primary.main" : "transparent",
                      }}
                    >
                      <Box className="space-y-1">
                        <div className="text-sm font-semibold">{row.title}</div>
                        <div className={cn("text-muted-foreground", densityConfig.metaTextClass)}>
                          {row.subtitle}
                        </div>
                      </Box>
                      <Box className="flex flex-wrap gap-2">
                        {row.chips.map((chip) => (
                          <div
                            key={chip}
                            className="rounded-full border border-border bg-muted px-2 py-0.5 text-xs"
                          >
                            {chip}
                          </div>
                        ))}
                      </Box>
                      <Box className="flex items-center justify-end gap-3">
                        <StatusPill status={row.status} mode={mode} />
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            {mode === "mui" ? (
                              <MuiIconButton size="small">...</MuiIconButton>
                            ) : mode === "wrapper" ? (
                              <AppIconButton label="More actions">...</AppIconButton>
                            ) : (
                              <Button size="icon" variant="ghost" aria-label="More actions">
                                ...
                              </Button>
                            )}
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Row actions</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem>Edit</DropdownMenuItem>
                            <DropdownMenuItem>Archive</DropdownMenuItem>
                            <DropdownMenuItem onSelect={() => setDialogOpen(true)}>
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </Box>
                    </LinearListRow>
                  );
                })}
              </div>
            </section>
            <section id="right-panel" className="space-y-4">
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Golden Patterns - RightPanel + Collapsible Sections
              </Typography>
              <div className="grid gap-4 lg:grid-cols-[1fr,360px]">
                <div className="rounded-lg border border-border bg-background p-4">
                  <EmptyState
                    title="Nothing selected"
                    description="Choose a row to see details in the right panel."
                    action={
                      mode === "mui" ? (
                        <MuiButton variant="outlined" size="small">
                          Create service
                        </MuiButton>
                      ) : mode === "wrapper" ? (
                        <AppButton variant="outline" size="sm">
                          Create service
                        </AppButton>
                      ) : (
                        <Button variant="outline" size="sm">
                          Create service
                        </Button>
                      )
                    }
                  />
                </div>
                <div className="space-y-3 rounded-lg border border-border bg-muted/40 p-3">
                  <RightPanelSection
                    title="Properties"
                    density={density}
                    action={
                      mode === "wrapper" ? (
                        <AppIconButton label="Edit properties">...</AppIconButton>
                      ) : mode === "mui" ? (
                        <MuiIconButton size="small">...</MuiIconButton>
                      ) : (
                        <Button size="icon" variant="ghost" aria-label="Edit properties">
                          ...
                        </Button>
                      )
                    }
                  >
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Service ID</span>
                        <span>SVC-001</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Lead</span>
                        <span>Ava</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Due</span>
                        <span>Mar 18</span>
                      </div>
                    </div>
                  </RightPanelSection>
                  <RightPanelSection title="Progress" density={density}>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Billed</span>
                        <span>$66k of $120k</span>
                      </div>
                      <LinearProgress variant="determinate" value={62} />
                    </div>
                  </RightPanelSection>
                  <RightPanelSection title="Activity" density={density}>
                    <div className="space-y-2 text-sm text-muted-foreground">
                      <div>Client asked for revision set.</div>
                      <div>Review cycle completed.</div>
                      <div>Updated drawing index posted.</div>
                    </div>
                  </RightPanelSection>
                </div>
              </div>
            </section>

            <section id="inline-edit" className="space-y-4">
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Golden Patterns - InlineEditableCell
              </Typography>
              <div className="rounded-lg border border-border bg-background p-4">
                <div className="grid gap-4 lg:grid-cols-3">
                  <div className="space-y-2">
                    <div className="text-xs uppercase text-muted-foreground">Text</div>
                    <InlineEditableCell
                      mode={mode}
                      type="text"
                      value={editableLabel}
                      dirty={editableLabel !== "Concept Set"}
                      onChange={(value) => setEditableLabel(String(value))}
                    />
                  </div>
                  <div className="space-y-2">
                    <div className="text-xs uppercase text-muted-foreground">Select</div>
                    <InlineEditableCell
                      mode={mode}
                      type="select"
                      value={editableStatus}
                      options={STATUS_OPTIONS}
                      dirty={editableStatus !== "Active"}
                      onChange={(value) => setEditableStatus(String(value))}
                    />
                  </div>
                  <div className="space-y-2">
                    <div className="text-xs uppercase text-muted-foreground">Toggle</div>
                    <InlineEditableCell
                      mode={mode}
                      type="toggle"
                      value={editableToggle}
                      dirty={editableToggle !== true}
                      onChange={(value) => setEditableToggle(Boolean(value))}
                    />
                  </div>
                </div>
              </div>
            </section>

            <section id="overlays" className="space-y-4">
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Overlays - Dialog + Dropdown/Menu
              </Typography>
              <div className="flex flex-wrap items-center gap-4 rounded-lg border border-border bg-background p-4">
                <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                  <DialogTrigger asChild>
                    {mode === "mui" ? (
                      <MuiButton variant="contained" color="error">
                        Confirm delete
                      </MuiButton>
                    ) : mode === "wrapper" ? (
                      <AppButton variant="destructive">Confirm delete</AppButton>
                    ) : (
                      <Button variant="destructive">Confirm delete</Button>
                    )}
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Delete service?</DialogTitle>
                      <DialogDescription>
                        This removes the service and its related items. This action cannot be undone.
                      </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                      {mode === "mui" ? (
                        <>
                          <MuiButton variant="outlined" onClick={() => setDialogOpen(false)}>
                            Cancel
                          </MuiButton>
                          <MuiButton variant="contained" color="error">
                            Delete
                          </MuiButton>
                        </>
                      ) : mode === "wrapper" ? (
                        <>
                          <AppButton variant="outline" onClick={() => setDialogOpen(false)}>
                            Cancel
                          </AppButton>
                          <AppButton variant="destructive">Delete</AppButton>
                        </>
                      ) : (
                        <>
                          <Button variant="outline" onClick={() => setDialogOpen(false)}>
                            Cancel
                          </Button>
                          <Button variant="destructive">Delete</Button>
                        </>
                      )}
                    </DialogFooter>
                  </DialogContent>
                </Dialog>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    {mode === "mui" ? (
                      <MuiButton variant="outlined">Open menu</MuiButton>
                    ) : mode === "wrapper" ? (
                      <AppButton variant="outline">Open menu</AppButton>
                    ) : (
                      <Button variant="outline">Open menu</Button>
                    )}
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start">
                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem>Edit</DropdownMenuItem>
                    <DropdownMenuItem>Archive</DropdownMenuItem>
                    <DropdownMenuItem onSelect={() => setDialogOpen(true)}>
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </section>

            <section id="kpi" className="space-y-4">
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                KPI - KpiStrip + KpiCard
              </Typography>
              <div className="grid gap-3 lg:grid-cols-4">
                {[
                  { label: "Agreed fee", value: "$540k", change: "+4%" },
                  { label: "Billed", value: "$320k", change: "+8%" },
                  { label: "Outstanding", value: "$220k", change: "-2%" },
                  { label: "Overdue", value: "$45k", change: "+1%" },
                ].map((kpi) =>
                  mode === "mui" ? (
                    <MuiCard key={kpi.label} variant="outlined">
                      <MuiCardContent sx={{ p: muiCardPadding }}>
                        <Typography variant="caption" color="text.secondary">
                          {kpi.label}
                        </Typography>
                        <Typography variant="h6">{kpi.value}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {kpi.change} vs last month
                        </Typography>
                      </MuiCardContent>
                    </MuiCard>
                  ) : mode === "wrapper" ? (
                    <AppCard key={kpi.label} title={kpi.label} density={density}>
                      <div className="text-2xl font-semibold">{kpi.value}</div>
                      <div className="text-xs text-muted-foreground">
                        {kpi.change} vs last month
                      </div>
                    </AppCard>
                  ) : (
                    <Card key={kpi.label} className="border border-border">
                      <CardHeader className={densityConfig.kpiPadding}>
                        <CardTitle className="text-sm font-medium">{kpi.label}</CardTitle>
                      </CardHeader>
                      <CardContent className={densityConfig.kpiPadding}>
                        <div className="text-2xl font-semibold">{kpi.value}</div>
                        <div className="text-xs text-muted-foreground">
                          {kpi.change} vs last month
                        </div>
                      </CardContent>
                    </Card>
                  )
                )}
              </div>
            </section>

            <section id="workspace" className="space-y-4">
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Workspace Mock - Services
              </Typography>
              <div className="rounded-xl border border-border bg-background">
                <div className="flex items-center justify-between border-b border-border px-5 py-4">
                  <div>
                    <div className="text-lg font-semibold">Services</div>
                    <div className="text-sm text-muted-foreground">
                      Linear list with right panel and inline editing.
                    </div>
                  </div>
                  {mode === "mui" ? (
                    <MuiButton variant="contained">New service</MuiButton>
                  ) : mode === "wrapper" ? (
                    <AppButton variant="primary">New service</AppButton>
                  ) : (
                    <Button>New service</Button>
                  )}
                </div>

                <div className="grid gap-0 lg:grid-cols-[1fr,360px]">
                  <div className="border-r border-border">
                    {workspaceRows.map((row) => {
                      const isSelected = row.id === selectedRowId;
                      return (
                        <LinearListRow
                          key={row.id}
                          columns={3}
                          onClick={() => setSelectedRowId(row.id)}
                          sx={{
                            py: densityConfig.rowPaddingY,
                            backgroundColor: isSelected ? "action.selected" : "background.paper",
                            borderLeft: isSelected ? "3px solid" : "3px solid transparent",
                            borderLeftColor: isSelected ? "primary.main" : "transparent",
                          }}
                        >
                          <Box className="space-y-1">
                            <div className="text-sm font-semibold">{row.title}</div>
                            <div
                              className={cn("text-muted-foreground", densityConfig.metaTextClass)}
                            >
                              {row.subtitle}
                            </div>
                          </Box>
                          <Box className="flex flex-wrap gap-2">
                            {row.chips.map((chip) => (
                              <div
                                key={chip}
                                className="rounded-full border border-border bg-muted px-2 py-0.5 text-xs"
                              >
                                {chip}
                              </div>
                            ))}
                          </Box>
                          <Box className="flex items-center justify-end gap-3">
                            <InlineEditableCell
                              mode={mode}
                              type="select"
                              value={row.editableStatus}
                              options={STATUS_OPTIONS}
                              dirty={row.editableDirty}
                              onChange={(value) => updateWorkspaceStatus(row.id, value as AppStatus)}
                            />
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                {mode === "mui" ? (
                                  <MuiIconButton size="small">...</MuiIconButton>
                                ) : mode === "wrapper" ? (
                                  <AppIconButton label="More actions">...</AppIconButton>
                                ) : (
                                  <Button size="icon" variant="ghost" aria-label="More actions">
                                    ...
                                  </Button>
                                )}
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem>Edit</DropdownMenuItem>
                                <DropdownMenuItem>Duplicate</DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onSelect={() => setDialogOpen(true)}>
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </Box>
                        </LinearListRow>
                      );
                    })}
                  </div>

                  <div className="max-h-[520px] overflow-auto bg-muted/30 p-4">
                    {selectedRow ? (
                      <div className="space-y-4">
                        <PanelCard
                          mode={mode}
                          density={density}
                          title="Properties"
                          subtitle={selectedRow.id}
                          actions={
                            mode === "mui" ? (
                              <MuiIconButton size="small">...</MuiIconButton>
                            ) : mode === "wrapper" ? (
                              <AppIconButton label="Edit properties">...</AppIconButton>
                            ) : (
                              <Button size="icon" variant="ghost" aria-label="Edit properties">
                                ...
                              </Button>
                            )
                          }
                        >
                          <div className="space-y-2 text-sm">
                            <div className="flex items-center justify-between">
                              <span className="text-muted-foreground">Owner</span>
                              <span>{selectedRow.owner}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-muted-foreground">Due</span>
                              <span>{selectedRow.due}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-muted-foreground">Status</span>
                              <span>{selectedRow.status}</span>
                            </div>
                          </div>
                        </PanelCard>

                        <PanelCard mode={mode} density={density} title="Progress">
                          <div className="space-y-3">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">Billed</span>
                              <span>
                                {selectedRow.billed} of {selectedRow.budget}
                              </span>
                            </div>
                            <LinearProgress variant="determinate" value={selectedRow.progress} />
                          </div>
                        </PanelCard>

                        <PanelCard mode={mode} density={density} title="Activity">
                          <div className="space-y-2 text-sm text-muted-foreground">
                            <div>Updated milestone schedule.</div>
                            <div>Uploaded coordination set.</div>
                            <div>Meeting held with consultant team.</div>
                          </div>
                        </PanelCard>

                        <PanelCard mode={mode} density={density} title="Notes">
                          {mode === "mui" ? (
                            <TextField
                              multiline
                              minRows={3}
                              defaultValue={selectedRow.notes}
                              fullWidth
                            />
                          ) : mode === "wrapper" ? (
                            <AppTextarea defaultValue={selectedRow.notes} />
                          ) : (
                            <Textarea defaultValue={selectedRow.notes} />
                          )}
                        </PanelCard>
                      </div>
                    ) : (
                      <EmptyState
                        title="Select a service"
                        description="Choose a row to see details and activity."
                      />
                    )}
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </Box>
  );
}
