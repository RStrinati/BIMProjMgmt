import { useState } from 'react';
import { DashboardShell, type DashboardWorkspace } from './DashboardShell';
import { AuditOverviewPanel } from './panels/AuditOverviewPanel';
import { IssuesPanel } from './panels/IssuesPanel';
import { ModelHealthPanel } from './panels/ModelHealthPanel';
import { ModelRegisterPanel } from './panels/ModelRegisterPanel';

export function DashboardWorkspacePage() {
  const [workspace, setWorkspace] = useState<DashboardWorkspace>('audit');

  return (
    <DashboardShell workspace={workspace} onWorkspaceChange={setWorkspace}>
      {workspace === 'audit' && <AuditOverviewPanel />}
      {workspace === 'issues' && <IssuesPanel />}
      {workspace === 'health' && <ModelHealthPanel />}
      {workspace === 'register' && <ModelRegisterPanel />}
    </DashboardShell>
  );
}
