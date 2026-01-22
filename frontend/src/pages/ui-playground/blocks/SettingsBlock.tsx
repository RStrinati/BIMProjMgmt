import { Bell, ShieldCheck, UserCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

export function SettingsBlock() {
  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Workspace settings</CardTitle>
            <CardDescription>Manage profile, notifications, and security.</CardDescription>
          </div>
          <Badge variant="outline">Admin</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 md:grid-cols-[1fr,2fr] md:items-center">
          <div className="flex items-center gap-2 text-sm font-medium">
            <UserCircle className="h-4 w-4 text-muted-foreground" />
            Profile
          </div>
          <div className="grid gap-3">
            <div className="grid gap-2">
              <Label htmlFor="settings-name">Name</Label>
              <Input id="settings-name" defaultValue="Ava Hernandez" />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="settings-email">Email</Label>
              <Input id="settings-email" type="email" defaultValue="ava@bimpjm.io" />
            </div>
          </div>
        </div>

        <Separator />

        <div className="grid gap-4 md:grid-cols-[1fr,2fr] md:items-center">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Bell className="h-4 w-4 text-muted-foreground" />
            Notifications
          </div>
          <div className="grid gap-3">
            <div className="grid gap-2">
              <Label htmlFor="settings-digest">Weekly digest</Label>
              <Input id="settings-digest" defaultValue="Monday, 9:00 AM" />
              <p className="text-xs text-muted-foreground">
                Summary of reviews, issues, and billing events.
              </p>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="settings-alerts">Critical alerts</Label>
              <Input id="settings-alerts" defaultValue="On hold, Overdue, Blocked" />
            </div>
          </div>
        </div>

        <Separator />

        <div className="grid gap-4 md:grid-cols-[1fr,2fr] md:items-center">
          <div className="flex items-center gap-2 text-sm font-medium">
            <ShieldCheck className="h-4 w-4 text-muted-foreground" />
            Security
          </div>
          <div className="grid gap-3">
            <div className="grid gap-2">
              <Label htmlFor="settings-role">Role</Label>
              <Input id="settings-role" defaultValue="Workspace Admin" />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline">Reset password</Button>
              <Button>Save changes</Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
