import { CalendarDays, Download, Filter, MoreHorizontal, TrendingUp, Users } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const stats = [
  { label: "Active projects", value: "24", change: "+8%" },
  { label: "Services in review", value: "12", change: "+3%" },
  { label: "Outstanding issues", value: "38", change: "-12%" },
  { label: "Billing this month", value: "$240k", change: "+5%" },
];

const activities = [
  {
    title: "Structural review cycle completed",
    detail: "Services · Tower B",
    badge: "Review",
  },
  {
    title: "RFI #128 closed",
    detail: "Issues · Podium",
    badge: "Resolved",
  },
  {
    title: "New deliverable uploaded",
    detail: "Deliverables · MEP",
    badge: "Upload",
  },
];

export function DashboardBlock() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-semibold text-foreground">Workspace Overview</h3>
          <p className="text-sm text-muted-foreground">Project health across services and reviews.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm">
            <CalendarDays className="mr-2 h-4 w-4" />
            This week
          </Button>
          <Button variant="outline" size="sm">
            <Filter className="mr-2 h-4 w-4" />
            Filters
          </Button>
          <Button size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label} className="border-border bg-card">
            <CardHeader className="pb-2">
              <CardDescription>{stat.label}</CardDescription>
              <CardTitle className="text-2xl">{stat.value}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <TrendingUp className="h-4 w-4 text-emerald-500" />
                {stat.change} vs last period
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="team">Team</TabsTrigger>
          <TabsTrigger value="billing">Billing</TabsTrigger>
        </TabsList>
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-[2fr,1fr]">
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle>Service progress</CardTitle>
                <CardDescription>Weekly delivery signals across disciplines.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  { label: "Architecture", value: 68 },
                  { label: "Structure", value: 44 },
                  { label: "MEP", value: 52 },
                  { label: "Façade", value: 82 },
                ].map((item) => (
                  <div key={item.label} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>{item.label}</span>
                      <span className="text-muted-foreground">{item.value}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted">
                      <div
                        className="h-2 rounded-full bg-primary"
                        style={{ width: `${item.value}%` }}
                      />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="border-border bg-card">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Team focus</CardTitle>
                  <CardDescription>Activity across packages</CardDescription>
                </div>
                <Users className="h-5 w-5 text-muted-foreground" />
              </CardHeader>
              <CardContent className="space-y-3">
                {activities.map((activity) => (
                  <div
                    key={activity.title}
                    className="flex items-start justify-between gap-3 rounded-lg border border-border bg-muted/40 p-3"
                  >
                    <div>
                      <div className="text-sm font-medium">{activity.title}</div>
                      <div className="text-xs text-muted-foreground">{activity.detail}</div>
                    </div>
                    <Badge variant="secondary">{activity.badge}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        <TabsContent value="team">
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>Team load</CardTitle>
              <CardDescription>Current allocation by discipline.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              {[
                { name: "Architecture", value: "42 hrs", status: "Active" },
                { name: "Structure", value: "31 hrs", status: "Blocked" },
                { name: "MEP", value: "28 hrs", status: "Active" },
                { name: "Interiors", value: "24 hrs", status: "On Hold" },
              ].map((row) => (
                <div
                  key={row.name}
                  className="flex items-center justify-between rounded-lg border border-border bg-background p-3"
                >
                  <div>
                    <div className="text-sm font-medium">{row.name}</div>
                    <div className="text-xs text-muted-foreground">{row.value} this week</div>
                  </div>
                  <Badge variant="outline">{row.status}</Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="billing">
          <Card className="border-border bg-card">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Billing approvals</CardTitle>
                <CardDescription>Invoices awaiting review.</CardDescription>
              </div>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" aria-label="More actions">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuLabel>Actions</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>Export CSV</DropdownMenuItem>
                  <DropdownMenuItem>Send reminder</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { name: "Tower A - Progress Claim", amount: "$46k", status: "Pending" },
                { name: "MEP Variation", amount: "$12k", status: "Review" },
                { name: "Facade Package", amount: "$38k", status: "Awaiting" },
              ].map((item) => (
                <div
                  key={item.name}
                  className="flex items-center justify-between rounded-lg border border-border bg-background p-3"
                >
                  <div>
                    <div className="text-sm font-medium">{item.name}</div>
                    <div className="text-xs text-muted-foreground">{item.amount}</div>
                  </div>
                  <Badge variant="secondary">{item.status}</Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
