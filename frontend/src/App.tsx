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
        <BrowserRouter>
          <MainLayout>
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/projects" element={<ProjectsPage />} />
              <Route path="/projects/:id" element={<ProjectDetailPage />} />
              <Route path="/projects/:id/data-imports" element={<DataImportsPage />} />
              <Route path="/data-imports" element={<DataImportsPage />} />
              <Route path="/reviews" element={<ComingSoonPage title="Reviews" />} />
              <Route path="/tasks" element={<ComingSoonPage title="Tasks" />} />
              <Route path="/analytics" element={<ComingSoonPage title="Analytics" />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </MainLayout>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

// Placeholder component for unimplemented pages
function ComingSoonPage({ title }: { title: string }) {
  return (
    <div style={{ textAlign: 'center', padding: '4rem' }}>
      <h1>{title}</h1>
      <p>This page is coming soon!</p>
    </div>
  );
}

export default App;
