import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Chip,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  AvatarGroup,
  Badge,
  Divider,
  LinearProgress,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@mui/material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RefreshIcon from '@mui/icons-material/Refresh';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';
import PersonIcon from '@mui/icons-material/Person';
import BugReportIcon from '@mui/icons-material/BugReport';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

// ==================== DATA TYPES ====================
interface SystemAlert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  action?: string;
}

interface ModelEvent {
  id: string;
  type: 'upload' | 'update' | 'review' | 'clash' | 'warning';
  title: string;
  description: string;
  timestamp: string;
  user: string;
  avatar?: string;
}

interface LiveMetric {
  name: string;
  value: number;
  unit: string;
  threshold: number;
  trend: number;
  status: 'normal' | 'warning' | 'critical';
}

interface PerformanceDataPoint {
  time: string;
  cpu: number;
  memory: number;
  diskIO: number;
  networkLatency: number;
}

// ==================== STYLED COMPONENTS ====================
const AlertBox: React.FC<{ alert: SystemAlert; onDismiss: () => void }> = ({
  alert,
  onDismiss,
}) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'success';
    }
  };

  return (
    <Alert
      severity={getSeverityColor(alert.severity) as any}
      onClose={onDismiss}
      sx={{ mb: 1 }}
      icon={
        alert.severity === 'critical' ? (
          <ErrorIcon />
        ) : alert.severity === 'warning' ? (
          <WarningIcon />
        ) : (
          <InfoIcon />
        )
      }
    >
      <AlertTitle sx={{ fontWeight: 600 }}>{alert.title}</AlertTitle>
      {alert.message}
      {alert.action && (
        <Box sx={{ mt: 1 }}>
          <Button size="small" variant="contained" sx={{ mr: 1 }}>
            {alert.action}
          </Button>
          <Button size="small" variant="outlined">
            Dismiss
          </Button>
        </Box>
      )}
    </Alert>
  );
};

const LiveMetricCard: React.FC<{ metric: LiveMetric }> = ({ metric }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical':
        return '#f44336';
      case 'warning':
        return '#FF9800';
      default:
        return '#4CAF50';
    }
  };

  const getThresholdColor = (value: number, threshold: number) => {
    if (value >= threshold * 0.8) return '#FF9800';
    if (value >= threshold) return '#f44336';
    return '#4CAF50';
  };

  return (
    <Card
      sx={{
        background: `linear-gradient(135deg, ${getStatusColor(metric.status)}15 0%, ${getStatusColor(metric.status)}05 100%)`,
        border: `2px solid ${getStatusColor(metric.status)}30`,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography color="textSecondary" variant="caption">
            {metric.name}
          </Typography>
          <FiberManualRecordIcon
            sx={{
              fontSize: '0.8rem',
              color: getStatusColor(metric.status),
              animation: metric.status !== 'normal' ? 'pulse 2s infinite' : 'none',
              '@keyframes pulse': {
                '0%': { opacity: 1 },
                '50%': { opacity: 0.5 },
                '100%': { opacity: 1 },
              },
            }}
          />
        </Box>
        <Box display="flex" alignItems="baseline" gap={1}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            {metric.value}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            {metric.unit}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={Math.min((metric.value / metric.threshold) * 100, 100)}
          sx={{
            mt: 1.5,
            height: 6,
            borderRadius: 3,
            backgroundColor: 'rgba(0,0,0,0.1)',
            '& .MuiLinearProgress-bar': {
              backgroundColor: getThresholdColor(metric.value, metric.threshold),
              borderRadius: 3,
            },
          }}
        />
        <Box display="flex" alignItems="center" gap={0.5} sx={{ mt: 1 }}>
          {metric.trend > 0 ? (
            <TrendingUpIcon sx={{ fontSize: '0.9rem', color: '#f44336' }} />
          ) : (
            <TrendingUpIcon
              sx={{
                fontSize: '0.9rem',
                color: '#4CAF50',
                transform: 'scaleY(-1)',
              }}
            />
          )}
          <Typography
            variant="caption"
            sx={{ color: metric.trend > 0 ? '#f44336' : '#4CAF50', fontWeight: 600 }}
          >
            {Math.abs(metric.trend)}%
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

const EventFeed: React.FC<{ events: ModelEvent[] }> = ({ events }) => (
  <Card sx={{ border: '1px solid rgba(0,0,0,0.08)' }}>
    <CardHeader title="Activity Feed" subtitle="Real-time model updates" />
    <CardContent sx={{ p: 0 }}>
      <List sx={{ maxHeight: '500px', overflow: 'auto' }}>
        {events.map((event, index) => (
          <React.Fragment key={event.id}>
            <ListItem
              sx={{
                '&:hover': { backgroundColor: 'rgba(0,0,0,0.02)' },
                px: 2,
                py: 1.5,
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <Tooltip title={event.type}>
                  <Avatar
                    sx={{
                      width: 32,
                      height: 32,
                      backgroundColor:
                        event.type === 'clash'
                          ? '#f44336'
                          : event.type === 'warning'
                          ? '#FF9800'
                          : event.type === 'upload'
                          ? '#2196F3'
                          : '#4CAF50',
                      fontSize: '0.8rem',
                    }}
                  >
                    {event.type === 'clash' && <BugReportIcon sx={{ fontSize: '1rem' }} />}
                    {event.type === 'upload' && <CloudUploadIcon sx={{ fontSize: '1rem' }} />}
                    {event.type === 'review' && <CheckCircleIcon sx={{ fontSize: '1rem' }} />}
                    {event.type === 'warning' && <WarningIcon sx={{ fontSize: '1rem' }} />}
                  </Avatar>
                </Tooltip>
              </ListItemIcon>
              <ListItemText
                primary={event.title}
                secondary={
                  <Box>
                    <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                      {event.description}
                    </Typography>
                    <Box display="flex" gap={1} alignItems="center" sx={{ mt: 0.5 }}>
                      <PersonIcon sx={{ fontSize: '0.75rem' }} />
                      <Typography variant="caption">{event.user}</Typography>
                      <Typography variant="caption" color="textSecondary">
                        • {event.timestamp}
                      </Typography>
                    </Box>
                  </Box>
                }
              />
            </ListItem>
            {index < events.length - 1 && <Divider />}
          </React.Fragment>
        ))}
      </List>
    </CardContent>
  </Card>
);

const PerformanceMonitor: React.FC<{ data: PerformanceDataPoint[] }> = ({ data }) => (
  <Card sx={{ border: '1px solid rgba(0,0,0,0.08)' }}>
    <CardHeader title="System Performance" subtitle="Last 24 hours" />
    <CardContent>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
          <XAxis dataKey="time" tick={{ fontSize: 12 }} />
          <YAxis stroke="rgba(0,0,0,0.5)" yAxisId="left" />
          <YAxis stroke="rgba(0,0,0,0.5)" yAxisId="right" orientation="right" />
          <ChartTooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #ccc',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="cpu"
            stroke="#2196F3"
            fill="#2196F3"
            fillOpacity={0.2}
            yAxisId="left"
            name="CPU %"
          />
          <Area
            type="monotone"
            dataKey="memory"
            stroke="#FF9800"
            fill="#FF9800"
            fillOpacity={0.2}
            yAxisId="left"
            name="Memory %"
          />
          <Area
            type="monotone"
            dataKey="networkLatency"
            stroke="#4CAF50"
            fill="#4CAF50"
            fillOpacity={0.2}
            yAxisId="right"
            name="Latency (ms)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </CardContent>
  </Card>
);

const UserActivityHeatmap: React.FC = () => {
  const heatmapData = [
    { hour: '00:00', activity: 5 },
    { hour: '02:00', activity: 8 },
    { hour: '04:00', activity: 3 },
    { hour: '06:00', activity: 2 },
    { hour: '08:00', activity: 45 },
    { hour: '10:00', activity: 78 },
    { hour: '12:00', activity: 92 },
    { hour: '14:00', activity: 85 },
    { hour: '16:00', activity: 72 },
    { hour: '18:00', activity: 58 },
    { hour: '20:00', activity: 42 },
    { hour: '22:00', activity: 18 },
  ];

  const getActivityColor = (value: number) => {
    if (value > 80) return '#1B5E20';
    if (value > 60) return '#4CAF50';
    if (value > 40) return '#FDD835';
    if (value > 20) return '#FF9800';
    return '#BDBDBD';
  };

  return (
    <Card sx={{ border: '1px solid rgba(0,0,0,0.08)' }}>
      <CardHeader title="User Activity Heatmap" subtitle="24-hour window" />
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={heatmapData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
            <XAxis dataKey="hour" tick={{ fontSize: 12 }} />
            <YAxis hide />
            <ChartTooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #ccc',
                borderRadius: '8px',
              }}
            />
            <Bar dataKey="activity" radius={[4, 4, 0, 0]}>
              {heatmapData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={getActivityColor(entry.activity)}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

// ==================== MAIN DASHBOARD ====================
const RealTimeMonitoringDashboard: React.FC = () => {
  const [dismissedAlerts, setDismissedAlerts] = useState<string[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [openDetailDialog, setOpenDetailDialog] = useState(false);

  // Sample data
  const alerts: SystemAlert[] = [
    {
      id: '1',
      severity: 'critical',
      title: 'High Clash Count Detected',
      message: 'MEP systems show 47 critical clashes with structural elements.',
      timestamp: '5 min ago',
      action: 'Review Clashes',
    },
    {
      id: '2',
      severity: 'warning',
      title: 'Incomplete Model Data',
      message: 'HVAC parametrization is 65% complete. Target: 85%',
      timestamp: '12 min ago',
      action: 'View Details',
    },
    {
      id: '3',
      severity: 'info',
      title: 'Model Update Available',
      message: 'Architectural model v2.3 uploaded by Sarah Johnson.',
      timestamp: '1 hour ago',
    },
  ];

  const liveMetrics: LiveMetric[] = [
    {
      name: 'Model Sync Health',
      value: 92,
      unit: '%',
      threshold: 100,
      trend: 2,
      status: 'normal',
    },
    {
      name: 'Active Clashes',
      value: 47,
      unit: 'items',
      threshold: 30,
      trend: 8,
      status: 'critical',
    },
    {
      name: 'Data Completeness',
      value: 78,
      unit: '%',
      threshold: 90,
      trend: -2,
      status: 'warning',
    },
    {
      name: 'System CPU Load',
      value: 68,
      unit: '%',
      threshold: 80,
      trend: 5,
      status: 'normal',
    },
  ];

  const events: ModelEvent[] = [
    {
      id: '1',
      type: 'clash',
      title: 'Critical Clash Detected',
      description: 'HVAC duct conflicts with structural column at Level 3',
      timestamp: '2 min ago',
      user: 'Sarah Johnson',
    },
    {
      id: '2',
      type: 'upload',
      title: 'Model Update Received',
      description: 'Structural model v3.1 - 45 elements updated',
      timestamp: '15 min ago',
      user: 'Mike Chen',
    },
    {
      id: '3',
      type: 'review',
      title: 'Review Completed',
      description: 'Architectural coordination review passed',
      timestamp: '1 hour ago',
      user: 'James Rodriguez',
    },
    {
      id: '4',
      type: 'warning',
      title: 'Data Quality Issue',
      description: 'Missing parameter values in electrical panel schedule',
      timestamp: '2 hours ago',
      user: 'Emma Taylor',
    },
  ];

  const performanceData: PerformanceDataPoint[] = [
    { time: '00:00', cpu: 45, memory: 62, diskIO: 25, networkLatency: 12 },
    { time: '04:00', cpu: 38, memory: 55, diskIO: 18, networkLatency: 9 },
    { time: '08:00', cpu: 72, memory: 78, diskIO: 65, networkLatency: 18 },
    { time: '12:00', cpu: 85, memory: 88, diskIO: 92, networkLatency: 32 },
    { time: '16:00', cpu: 78, memory: 82, diskIO: 78, networkLatency: 28 },
    { time: '20:00', cpu: 62, memory: 70, diskIO: 48, networkLatency: 16 },
    { time: '23:59', cpu: 48, memory: 60, diskIO: 30, networkLatency: 11 },
  ];

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1000);
  };

  const visibleAlerts = alerts.filter((a) => !dismissedAlerts.includes(a.id));

  return (
    <Box sx={{ p: 3, background: '#f5f7fa', minHeight: '100vh' }}>
      {/* HEADER */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            Real-Time Monitoring
          </Typography>
          <Box display="flex" alignItems="center" gap={1}>
            <FiberManualRecordIcon
              sx={{
                fontSize: '0.8rem',
                color: '#4CAF50',
                animation: 'pulse 2s infinite',
                '@keyframes pulse': {
                  '0%': { opacity: 1 },
                  '50%': { opacity: 0.5 },
                  '100%': { opacity: 1 },
                },
              }}
            />
            <Typography color="textSecondary" variant="body2">
              Live monitoring active
            </Typography>
          </Box>
        </Box>
        <Tooltip title="Refresh data">
          <IconButton onClick={handleRefresh} disabled={refreshing}>
            <RefreshIcon sx={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
          </IconButton>
        </Tooltip>
      </Box>

      {/* ALERTS */}
      {visibleAlerts.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Box display="flex" alignItems="center" gap={1} mb={2}>
            <NotificationsActiveIcon sx={{ color: '#f44336' }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              System Alerts
            </Typography>
            <Chip label={visibleAlerts.length} size="small" color="error" />
          </Box>
          {visibleAlerts.map((alert) => (
            <AlertBox
              key={alert.id}
              alert={alert}
              onDismiss={() =>
                setDismissedAlerts([...dismissedAlerts, alert.id])
              }
            />
          ))}
        </Box>
      )}

      {/* LIVE METRICS */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
          Live Metrics
        </Typography>
        <Grid container spacing={2}>
          {liveMetrics.map((metric) => (
            <Grid item xs={12} sm={6} md={3} key={metric.name}>
              <LiveMetricCard metric={metric} />
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* MAIN MONITORING SECTION */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <PerformanceMonitor data={performanceData} />
        </Grid>
        <Grid item xs={12} md={4}>
          <UserActivityHeatmap />
        </Grid>
      </Grid>

      {/* ACTIVITY FEED */}
      <Box sx={{ mt: 3 }}>
        <EventFeed events={events} />
      </Box>
    </Box>
  );
};

export default RealTimeMonitoringDashboard;
// @ts-nocheck
