import React, { useState, useEffect } from 'react';
import { Container, CircularProgress, Box, Alert } from '@mui/material';
import ModernDashboard from './ModernDashboard';
import AnalyticsDashboard from './AnalyticsDashboard';
import RealTimeMonitoringDashboard from './RealTimeMonitoringDashboard';

// ==================== TYPES ====================
interface DashboardData {
  projects: any[];
  healthData: any[];
  reviewPhaseData: any[];
  issueData: any[];
  issueHistory: any[];
  disciplineData: any[];
  qualityData: any[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

// ==================== API INTEGRATION ====================

/**
 * Fetch project metrics from backend
 */
const fetchProjectMetrics = async (): Promise<any[]> => {
  try {
    const response = await fetch('/api/projects/metrics');
    if (!response.ok) throw new Error('Failed to fetch projects');
    return response.json();
  } catch (error) {
    console.error('Error fetching projects:', error);
    throw error;
  }
};

/**
 * Fetch health metrics for a project
 */
const fetchHealthMetrics = async (projectId: number): Promise<any[]> => {
  try {
    const response = await fetch(`/api/projects/${projectId}/health-metrics`);
    if (!response.ok) throw new Error('Failed to fetch health metrics');
    return response.json();
  } catch (error) {
    console.error('Error fetching health metrics:', error);
    throw error;
  }
};

/**
 * Fetch review phase data
 */
const fetchReviewPhaseData = async (projectId: number): Promise<any[]> => {
  try {
    const response = await fetch(`/api/projects/${projectId}/reviews/phases`);
    if (!response.ok) throw new Error('Failed to fetch review phases');
    return response.json();
  } catch (error) {
    console.error('Error fetching review phases:', error);
    throw error;
  }
};

/**
 * Fetch issue data by category
 */
const fetchIssueData = async (projectId: number): Promise<any[]> => {
  try {
    const response = await fetch(`/api/projects/${projectId}/issues/breakdown`);
    if (!response.ok) throw new Error('Failed to fetch issues');
    return response.json();
  } catch (error) {
    console.error('Error fetching issues:', error);
    throw error;
  }
};

/**
 * Fetch weekly issue history by status
 */
const fetchIssueHistory = async (projectId: number): Promise<any[]> => {
  try {
    const response = await fetch(`/api/dashboard/issues-history?project_ids=${projectId}`);
    if (!response.ok) throw new Error('Failed to fetch issues history');
    const data = await response.json();
    return data.items || [];
  } catch (error) {
    console.error('Error fetching issues history:', error);
    throw error;
  }
};

/**
 * Fetch discipline performance data
 */
const fetchDisciplinePerformance = async (projectId: number): Promise<any[]> => {
  try {
    const response = await fetch(`/api/projects/${projectId}/discipline-performance`);
    if (!response.ok) throw new Error('Failed to fetch discipline data');
    return response.json();
  } catch (error) {
    console.error('Error fetching discipline data:', error);
    throw error;
  }
};

/**
 * Fetch model quality data
 */
const fetchModelQuality = async (projectId: number): Promise<any[]> => {
  try {
    const response = await fetch(`/api/projects/${projectId}/model-quality`);
    if (!response.ok) throw new Error('Failed to fetch model quality');
    return response.json();
  } catch (error) {
    console.error('Error fetching model quality:', error);
    throw error;
  }
};

// ==================== MAIN COMPONENT ====================

interface DashboardContainerProps {
  projectId?: number;
  dashboardType?: 'modern' | 'analytics' | 'realtime' | 'all';
  autoRefreshInterval?: number; // in milliseconds
}

/**
 * DashboardContainer - Manages data fetching and dashboard rendering
 * 
 * Usage:
 * <DashboardContainer projectId={1} dashboardType="modern" autoRefreshInterval={30000} />
 */
export const DashboardContainer: React.FC<DashboardContainerProps> = ({
  projectId = 1,
  dashboardType = 'modern',
  autoRefreshInterval = 30000,
}) => {
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    projects: [],
    healthData: [],
    reviewPhaseData: [],
    issueData: [],
    issueHistory: [],
    disciplineData: [],
    qualityData: [],
    loading: true,
    error: null,
    lastUpdated: null,
  });

  // Fetch all dashboard data
  const loadDashboardData = async () => {
    try {
      setDashboardData((prev) => ({ ...prev, loading: true, error: null }));

      const [
        projects,
        healthData,
        reviewPhaseData,
        issueData,
        issueHistory,
        disciplineData,
        qualityData,
      ] = await Promise.all([
        fetchProjectMetrics(),
        fetchHealthMetrics(projectId),
        fetchReviewPhaseData(projectId),
        fetchIssueData(projectId),
        fetchIssueHistory(projectId),
        fetchDisciplinePerformance(projectId),
        fetchModelQuality(projectId),
      ]);

      setDashboardData({
        projects,
        healthData,
        reviewPhaseData,
        issueData,
        issueHistory,
        disciplineData,
        qualityData,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setDashboardData((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
    }
  };

  // Initial data load
  useEffect(() => {
    loadDashboardData();
  }, [projectId]);

  // Auto-refresh interval
  useEffect(() => {
    if (!autoRefreshInterval) return;

    const interval = setInterval(() => {
      loadDashboardData();
    }, autoRefreshInterval);

    return () => clearInterval(interval);
  }, [autoRefreshInterval, projectId]);

  // Loading state
  if (dashboardData.loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (dashboardData.error) {
    return (
      <Container sx={{ mt: 4 }}>
        <Alert severity="error">
          Failed to load dashboard: {dashboardData.error}
        </Alert>
      </Container>
    );
  }

  // Render selected dashboard(s)
  return (
    <Box>
      {(dashboardType === 'modern' || dashboardType === 'all') && (
        <ModernDashboard
          projects={dashboardData.projects}
          healthData={dashboardData.healthData}
          reviewPhaseData={dashboardData.reviewPhaseData}
          issueData={dashboardData.issueData}
          issueHistory={dashboardData.issueHistory}
        />
      )}

      {(dashboardType === 'analytics' || dashboardType === 'all') && (
        <AnalyticsDashboard />
      )}

      {(dashboardType === 'realtime' || dashboardType === 'all') && (
        <RealTimeMonitoringDashboard />
      )}
    </Box>
  );
};

// ==================== HOOK FOR DASHBOARD DATA ====================

/**
 * Hook to use dashboard data with automatic refresh
 * 
 * Usage:
 * const { projects, healthData, loading, error, refresh } = useDashboardData(projectId);
 */
export const useDashboardData = (projectId: number, autoRefresh = true) => {
  const [data, setData] = useState<DashboardData>({
    projects: [],
    healthData: [],
    reviewPhaseData: [],
    issueData: [],
    issueHistory: [],
    disciplineData: [],
    qualityData: [],
    loading: true,
    error: null,
    lastUpdated: null,
  });

  const refresh = async () => {
    try {
      setData((prev) => ({ ...prev, loading: true }));

      const [
        projects,
        healthData,
        reviewPhaseData,
        issueData,
        issueHistory,
        disciplineData,
        qualityData,
      ] = await Promise.all([
        fetchProjectMetrics(),
        fetchHealthMetrics(projectId),
        fetchReviewPhaseData(projectId),
        fetchIssueData(projectId),
        fetchIssueHistory(projectId),
        fetchDisciplinePerformance(projectId),
        fetchModelQuality(projectId),
      ]);

      setData({
        projects,
        healthData,
        reviewPhaseData,
        issueData,
        issueHistory,
        disciplineData,
        qualityData,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setData((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
    }
  };

  useEffect(() => {
    refresh();

    if (!autoRefresh) return;

    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [projectId]);

  return { ...data, refresh };
};

// ==================== EXAMPLE USAGE ====================

/**
 * Example: Using dashboard in a page component
 * 
 * export default function ProjectDashboardPage() {
 *   return (
 *     <DashboardContainer
 *       projectId={1}
 *       dashboardType="modern"
 *       autoRefreshInterval={30000}
 *     />
 *   );
 * }
 */

/**
 * Example: Using with custom hook
 * 
 * export default function CustomDashboard() {
 *   const { projects, healthData, loading, error, refresh } = useDashboardData(1);
 *   
 *   if (loading) return <CircularProgress />;
 *   if (error) return <Alert severity="error">{error}</Alert>;
 *   
 *   return (
 *     <>
 *       <ModernDashboard projects={projects} healthData={healthData} />
 *       <Button onClick={refresh}>Refresh Data</Button>
 *     </>
 *   );
 * }
 */

export default DashboardContainer;
