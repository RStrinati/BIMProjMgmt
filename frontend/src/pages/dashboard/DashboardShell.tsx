import { useMemo, useState } from 'react';
import { Box, Drawer, IconButton, Stack, Tab, Tabs, Typography, useMediaQuery } from '@mui/material';
import GlobalStyles from '@mui/material/GlobalStyles';
import MenuIcon from '@mui/icons-material/Menu';
import { ThemeProvider } from '@mui/material/styles';
import { dashboardTheme } from '@/components/dashboards/themes';
import { DashboardFiltersProvider } from './DashboardFiltersContext';
import { DashboardFilterRail } from './DashboardFilterRail';
import { FilterSummaryBar } from './FilterSummaryBar';
import './dashboard.css';

export type DashboardWorkspace = 'audit' | 'issues' | 'health' | 'register';

const WORKSPACES: { key: DashboardWorkspace; label: string; description: string }[] = [
  { key: 'audit', label: 'Audit Overview', description: 'Naming + coordinate compliance' },
  { key: 'issues', label: 'Issues', description: 'Coordination risks' },
  { key: 'health', label: 'Model Health', description: 'Deep diagnostics' },
  { key: 'register', label: 'Model Register', description: 'Latest models and freshness' },
];

export function DashboardShell({
  workspace,
  onWorkspaceChange,
  children,
}: {
  workspace: DashboardWorkspace;
  onWorkspaceChange: (next: DashboardWorkspace) => void;
  children: React.ReactNode;
}) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const isDesktop = useMediaQuery(dashboardTheme.breakpoints.up('lg'));
  const activeIndex = useMemo(() => {
    const idx = WORKSPACES.findIndex((item) => item.key === workspace);
    return idx >= 0 ? idx : 0;
  }, [workspace]);
  const activeWorkspace = WORKSPACES[activeIndex] ?? WORKSPACES[0];

  return (
    <ThemeProvider theme={dashboardTheme}>
      <GlobalStyles
        styles={{
          body: {
            backgroundColor: dashboardTheme.palette.background.default,
          },
          '.dashboard-root': {
            fontFamily: dashboardTheme.typography.fontFamily,
          },
        }}
      />
      <DashboardFiltersProvider>
        <Box className="dashboard-root dashboard-grid" sx={{ position: 'relative', minHeight: '100vh' }}>
          <Box className="dashboard-glow" />
          <Stack direction={{ xs: 'column', lg: 'row' }} spacing={3} sx={{ px: { xs: 2, md: 3 }, py: 3 }}>
            {isDesktop ? (
              <Box sx={{ width: 280, flexShrink: 0 }}>
                <DashboardFilterRail />
              </Box>
            ) : (
              <Drawer open={drawerOpen} onClose={() => setDrawerOpen(false)} PaperProps={{ sx: { width: 280, p: 2 } }}>
                <DashboardFilterRail />
              </Drawer>
            )}

            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Stack spacing={2} sx={{ mb: 2 }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Stack spacing={0.5}>
                    <Typography variant="h4">Dashboard</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {activeWorkspace.description}
                    </Typography>
                  </Stack>
                  {!isDesktop ? (
                    <IconButton onClick={() => setDrawerOpen(true)} sx={{ color: 'text.primary' }}>
                      <MenuIcon />
                    </IconButton>
                  ) : null}
                </Stack>

                <Tabs
                  value={activeIndex}
                  onChange={(_, value) => onWorkspaceChange(WORKSPACES[value]?.key ?? 'audit')}
                  textColor="inherit"
                  indicatorColor="primary"
                >
                  {WORKSPACES.map((item) => (
                    <Tab key={item.key} label={item.label} />
                  ))}
                </Tabs>

                <FilterSummaryBar />
              </Stack>
              {children}
            </Box>
          </Stack>
        </Box>
      </DashboardFiltersProvider>
    </ThemeProvider>
  );
}
