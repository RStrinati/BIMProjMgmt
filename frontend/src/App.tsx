import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { theme } from './theme/theme';
import { MainLayout } from './components/layout/MainLayout';
import { DashboardPage } from './pages/DashboardPage';
import { ProjectsPage } from './pages/ProjectsPage';
import ProjectDetailPage from './pages/ProjectDetailPage';
import DataImportsPage from './pages/DataImportsPage';
import SettingsPage from './pages/SettingsPage';
import TasksNotesPage from './pages/TasksNotesPage';
import { BidsListPage } from './pages/BidsListPage';
import BidDetailPage from './pages/BidDetailPage';
import ProjectWorkspacePageV2 from './pages/ProjectWorkspacePageV2';
import WorkspaceShell from './pages/WorkspaceShell';
import OverviewTab from './pages/workspace/OverviewTab';
import ServicesTab from './pages/workspace/ServicesTab';
import ServiceEditView from './pages/workspace/ServiceEditView';
import DeliverablesTab from './pages/workspace/DeliverablesTab';
import UpdatesTab from './pages/workspace/UpdatesTab';
import IssuesTab from './pages/workspace/IssuesTab';
import TasksTab from './pages/workspace/TasksTab';
import QualityTab from './pages/workspace/QualityTab';
import ServiceCreateView from './pages/workspace/ServiceCreateView';
import { IssuesPage } from './pages/IssuesPage';
import { featureFlags } from './config/featureFlags';
import UiPlaygroundPage from './pages/UiPlaygroundPage';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <MainLayout>
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/projects" element={<ProjectsPage />} />
              
              {/* Workspace with nested routes */}
              <Route path="/projects/:id/workspace" element={<WorkspaceShell />}>
                <Route index element={<Navigate to="overview" replace />} />
                <Route path="overview" element={<OverviewTab />} />
                <Route path="services" element={<ServicesTab />} />
                <Route path="services/new" element={<ServiceCreateView />} />
                <Route path="services/:serviceId" element={<ServiceEditView />} />
                <Route path="deliverables" element={<DeliverablesTab />} />
                <Route path="updates" element={<UpdatesTab />} />
                <Route path="issues" element={<IssuesTab />} />
                <Route path="tasks" element={<TasksTab />} />
                <Route path="quality" element={<QualityTab />} />
              </Route>
              
              {/* Legacy route - redirect to workspace */}
              <Route 
                path="/projects/:id" 
                element={<Navigate to="workspace/overview" replace />} 
              />
              
              <Route path="/projects/:id/data-imports" element={<DataImportsPage />} />
              <Route path="/data-imports" element={<DataImportsPage />} />
              <Route path="/bids" element={<BidsListPage />} />
              <Route path="/bids/:id" element={<BidDetailPage />} />
              {featureFlags.issuesHub && <Route path="/issues" element={<IssuesPage />} />}
              <Route path="/reviews" element={<Navigate to="/projects" replace />} />
              <Route path="/tasks" element={<TasksNotesPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/ui" element={<UiPlaygroundPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </MainLayout>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
