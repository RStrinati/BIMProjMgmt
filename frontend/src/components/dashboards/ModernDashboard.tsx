import React, { useState, useMemo } from 'react';
import {
  Grid,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Paper,
  Tooltip,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
} from 'recharts';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import BuildIcon from '@mui/icons-material/Build';

// ==================== DATA INTERFACES ====================
interface ProjectMetrics {
  projectId: number;
  projectName: string;
  reviewCycles: number;
  completionRate: number;
  activeIssues: number;
  healthScore: number;
  status: 'on-track' | 'at-risk' | 'critical';
}

interface BIMHealthData {
  date: string;
  modelHealth: number;
  issueCount: number;
  elementCount: number;
}

interface ReviewPhaseData {
  phase: string;
  planned: number;
  actual: number;
  variance: number;
}

interface IssueCategoryBreakdown {
  category: string;
  count: number;
  severity: 'low' | 'medium' | 'high';
}

// ==================== STYLED COMPONENTS ====================
const StatCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: number;
  icon?: React.ReactNode;
  color?: string;
}> = ({ title, value, subtitle, trend, icon, color = '#1976d2' }) => (
  <Card
    sx={{
      height: '100%',
      background: `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)`,
      border: `2px solid ${color}30`,
      transition: 'all 0.3s ease',
      '&:hover': {
        transform: 'translateY(-4px)',
        boxShadow: `0 12px 24px ${color}20`,
      },
    }}
  >
    <CardContent>
      <Box display="flex" justifyContent="space-between" alignItems="flex-start">
        <Box>
          <Typography color="textSecondary" gutterBottom variant="caption">
            {title}
          </Typography>
          <Typography variant="h5" sx={{ fontWeight: 700, color }}>
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
              {subtitle}
            </Typography>
          )}
          {trend !== undefined && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1 }}>
              <TrendingUpIcon
                sx={{
                  fontSize: '1rem',
                  color: trend > 0 ? '#4caf50' : '#f44336',
                  transform: trend < 0 ? 'scaleY(-1)' : 'none',
                }}
              />
              <Typography
                variant="caption"
                sx={{ color: trend > 0 ? '#4caf50' : '#f44336', fontWeight: 600 }}
              >
                {Math.abs(trend)}%
              </Typography>
            </Box>
          )}
        </Box>
        {icon && (
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: '12px',
              background: `${color}20`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color,
            }}
          >
            {icon}
          </Box>
        )}
      </Box>
    </CardContent>
  </Card>
);

const ChartCard: React.FC<{
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  actionMenu?: Array<{ label: string; onClick: () => void }>;
}> = ({ title, subtitle, children, actionMenu }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        border: '1px solid rgba(0,0,0,0.08)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        transition: 'box-shadow 0.3s ease',
        '&:hover': {
          boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
        },
      }}
    >
      <CardHeader
        title={title}
        subheader={subtitle}
        action={
          actionMenu && (
            <>
              <IconButton size="small" onClick={handleMenuOpen}>
                <MoreVertIcon fontSize="small" />
              </IconButton>
              <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
                {actionMenu.map((item) => (
                  <MenuItem
                    key={item.label}
                    onClick={() => {
                      item.onClick();
                      handleMenuClose();
                    }}
                  >
                    {item.label}
                  </MenuItem>
                ))}
              </Menu>
            </>
          )
        }
        sx={{
          '& .MuiCardHeader-title': { fontSize: '1.1rem', fontWeight: 600 },
          '& .MuiCardHeader-subheader': { fontSize: '0.85rem' },
        }}
      />
      <CardContent sx={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
        {children}
      </CardContent>
    </Card>
  );
};

// ==================== DASHBOARD COMPONENTS ====================
const HealthTrendChart: React.FC<{ data: BIMHealthData[] }> = ({ data }) => (
  <ChartCard title="Model Health Trend" subtitle="30-day progression">
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12 }}
          stroke="rgba(0,0,0,0.5)"
        />
        <YAxis stroke="rgba(0,0,0,0.5)" />
        <ChartTooltip
          contentStyle={{
            backgroundColor: '#fff',
            border: '1px solid #ccc',
            borderRadius: '8px',
          }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="modelHealth"
          stroke="#2196F3"
          dot={{ fill: '#2196F3', r: 4 }}
          activeDot={{ r: 6 }}
          strokeWidth={2}
          name="Health Score %"
        />
        <Line
          type="monotone"
          dataKey="issueCount"
          stroke="#FF9800"
          yAxisId="right"
          dot={{ fill: '#FF9800', r: 4 }}
          name="Active Issues"
          strokeWidth={2}
        />
      </LineChart>
    </ResponsiveContainer>
  </ChartCard>
);

const ReviewPhaseComparison: React.FC<{ data: ReviewPhaseData[] }> = ({ data }) => (
  <ChartCard title="Review Phase Variance" subtitle="Planned vs Actual Timeline">
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
        <XAxis dataKey="phase" tick={{ fontSize: 12 }} />
        <YAxis stroke="rgba(0,0,0,0.5)" />
        <ChartTooltip
          contentStyle={{
            backgroundColor: '#fff',
            border: '1px solid #ccc',
            borderRadius: '8px',
          }}
        />
        <Legend />
        <Bar dataKey="planned" fill="#4CAF50" radius={[8, 8, 0, 0]} />
        <Bar dataKey="actual" fill="#2196F3" radius={[8, 8, 0, 0]} />
        <Bar
          dataKey="variance"
          fill="#FF6B6B"
          radius={[8, 8, 0, 0]}
          name="Variance (Days)"
        />
      </BarChart>
    </ResponsiveContainer>
  </ChartCard>
);

const IssueSeverityBreakdown: React.FC<{ data: IssueCategoryBreakdown[] }> = ({
  data,
}) => {
  const COLORS: Record<string, string> = {
    high: '#f44336',
    medium: '#ff9800',
    low: '#4caf50',
  };

  return (
    <ChartCard title="Issues by Severity" subtitle="Distribution across categories">
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={(entry: IssueCategoryBreakdown) => `${entry.category}: ${entry.count}`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="count"
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[entry.severity]}
              />
            ))}
          </Pie>
          <ChartTooltip />
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  );
};

const ProjectScatterMatrix: React.FC<{
  projects: ProjectMetrics[];
}> = ({ projects }) => (
  <ChartCard
    title="Project Performance Matrix"
    subtitle="Health Score vs Completion Rate"
  >
    <ResponsiveContainer width="100%" height={300}>
      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
        <XAxis
          type="number"
          dataKey="completionRate"
          name="Completion %"
          stroke="rgba(0,0,0,0.5)"
        />
        <YAxis
          type="number"
          dataKey="healthScore"
          name="Health Score"
          stroke="rgba(0,0,0,0.5)"
        />
        <ChartTooltip
          cursor={{ strokeDasharray: '3 3' }}
          contentStyle={{
            backgroundColor: '#fff',
            border: '1px solid #ccc',
            borderRadius: '8px',
          }}
        />
        <Scatter
          name="Projects"
          data={projects}
          fill="#8884d8"
          fillOpacity={0.7}
        />
      </ScatterChart>
    </ResponsiveContainer>
  </ChartCard>
);

const ProjectStatusGrid: React.FC<{ projects: ProjectMetrics[] }> = ({
  projects,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'on-track':
        return '#4CAF50';
      case 'at-risk':
        return '#FF9800';
      case 'critical':
        return '#f44336';
      default:
        return '#757575';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'on-track':
        return <CheckCircleIcon />;
      case 'at-risk':
        return <WarningIcon />;
      case 'critical':
        return <WarningIcon />;
      default:
        return <BuildIcon />;
    }
  };

  return (
    <Card sx={{ border: '1px solid rgba(0,0,0,0.08)' }}>
      <CardHeader title="Project Status Overview" />
      <CardContent>
        <Grid container spacing={2}>
          {projects.map((project) => (
            <Grid item xs={12} sm={6} md={4} key={project.projectId}>
              <Paper
                sx={{
                  p: 2,
                  borderLeft: `4px solid ${getStatusColor(project.status)}`,
                  transition: 'all 0.3s ease',
                  cursor: 'pointer',
                  '&:hover': {
                    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                    transform: 'translateY(-2px)',
                  },
                }}
              >
                <Box display="flex" justifyContent="space-between" alignItems="start">
                  <Box flex={1}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      {project.projectName}
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      <Box display="flex" gap={1} mb={1}>
                        <Chip
                          label={`${project.completionRate}% Complete`}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={`${project.activeIssues} Issues`}
                          size="small"
                          color={
                            project.activeIssues > 10 ? 'error' : 'default'
                          }
                          variant="filled"
                        />
                      </Box>
                      <Typography variant="caption" color="textSecondary">
                        Health: {project.healthScore}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={project.healthScore}
                        sx={{ mt: 1, mb: 1 }}
                      />
                    </Box>
                  </Box>
                  <Tooltip title={project.status}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: getStatusColor(project.status),
                        ml: 1,
                      }}
                    >
                      {getStatusIcon(project.status)}
                    </Box>
                  </Tooltip>
                </Box>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

// ==================== MAIN DASHBOARD ====================
interface ModernDashboardProps {
  projects?: ProjectMetrics[];
  healthData?: BIMHealthData[];
  reviewPhaseData?: ReviewPhaseData[];
  issueData?: IssueCategoryBreakdown[];
}

export const ModernDashboard: React.FC<ModernDashboardProps> = ({
  projects = [],
  healthData = [],
  reviewPhaseData = [],
  issueData = [],
}) => {
  // Sample data if none provided
  const sampleProjects: ProjectMetrics[] = projects.length > 0 ? projects : [
    {
      projectId: 1,
      projectName: 'Downtown Tower',
      reviewCycles: 4,
      completionRate: 75,
      activeIssues: 12,
      healthScore: 82,
      status: 'on-track',
    },
    {
      projectId: 2,
      projectName: 'Transit Hub',
      reviewCycles: 3,
      completionRate: 45,
      activeIssues: 28,
      healthScore: 65,
      status: 'at-risk',
    },
  ];

  const sampleHealthData: BIMHealthData[] = healthData.length > 0 ? healthData : [
    { date: '2025-01-01', modelHealth: 78, issueCount: 45, elementCount: 12500 },
    { date: '2025-01-05', modelHealth: 82, issueCount: 38, elementCount: 12500 },
    { date: '2025-01-10', modelHealth: 80, issueCount: 42, elementCount: 13200 },
  ];

  const sampleReviewPhaseData: ReviewPhaseData[] = reviewPhaseData.length > 0 ? reviewPhaseData : [
    { phase: 'Conceptual', planned: 15, actual: 18, variance: 3 },
    { phase: 'Schematic', planned: 25, actual: 23, variance: -2 },
  ];

  const sampleIssueData: IssueCategoryBreakdown[] = issueData.length > 0 ? issueData : [
    { category: 'Structural', count: 28, severity: 'high' },
    { category: 'MEP', count: 45, severity: 'medium' },
    { category: 'Coordination', count: 12, severity: 'low' },
  ];

  const stats = useMemo(() => ({
    totalProjects: sampleProjects.length,
    avgHealth: Math.round(
      sampleProjects.reduce((sum, p) => sum + p.healthScore, 0) / sampleProjects.length
    ),
    totalIssues: sampleProjects.reduce((sum, p) => sum + p.activeIssues, 0),
    avgCompletion: Math.round(
      sampleProjects.reduce((sum, p) => sum + p.completionRate, 0) / sampleProjects.length
    ),
  }), [sampleProjects]);

  return (
    <Box sx={{ p: 3, background: '#f5f7fa', minHeight: '100vh' }}>
      {/* HEADER */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          BIM Project Dashboard
        </Typography>
        <Typography color="textSecondary">
          Real-time project performance and model health metrics
        </Typography>
      </Box>

      {/* KEY METRICS ROW */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Projects"
            value={stats.totalProjects}
            color="#2196F3"
            icon={<BuildIcon />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Health Score"
            value={`${stats.avgHealth}%`}
            trend={5}
            color="#4CAF50"
            icon={<CheckCircleIcon />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Issues"
            value={stats.totalIssues}
            trend={-8}
            color="#FF9800"
            icon={<WarningIcon />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Completion"
            value={`${stats.avgCompletion}%`}
            trend={12}
            color="#9C27B0"
            icon={<TrendingUpIcon />}
          />
        </Grid>
      </Grid>

      {/* MAIN CHARTS ROW */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <HealthTrendChart data={sampleHealthData} />
        </Grid>
        <Grid item xs={12} md={6}>
          <ReviewPhaseComparison data={sampleReviewPhaseData} />
        </Grid>
      </Grid>

      {/* SECONDARY CHARTS ROW */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <IssueSeverityBreakdown data={sampleIssueData} />
        </Grid>
        <Grid item xs={12} md={8}>
          <ProjectScatterMatrix projects={sampleProjects} />
        </Grid>
      </Grid>

      {/* PROJECT GRID */}
      <ProjectStatusGrid projects={sampleProjects} />
    </Box>
  );
};

export default ModernDashboard;
