import React, { useState } from 'react';
import {
  Grid,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Chip,
  Button,
  ButtonGroup,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Avatar,
  AvatarGroup,
  Tabs,
  Tab,
  LinearProgress,
} from '@mui/material';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  HeatMap,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Line,
} from 'recharts';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineOppositeContent,
  TimelineDot,
} from '@mui/lab';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

// ==================== DATA TYPES ====================
interface TimelineEvent {
  date: string;
  milestone: string;
  status: 'completed' | 'in-progress' | 'pending';
  daysOverdue?: number;
}

interface DisciplinePerformance {
  discipline: string;
  coordinationScore: number;
  clashCount: number;
  resolutionRate: number;
  trend: number;
}

interface ElementQuality {
  type: string;
  modelCompleteness: number;
  dataAccuracy: number;
  parametrization: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`tabpanel-${index}`}
    aria-labelledby={`tab-${index}`}
  >
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

// ==================== STYLED COMPONENTS ====================
const PerformanceRadar: React.FC<{ disciplines: DisciplinePerformance[] }> = ({
  disciplines,
}) => (
  <Card sx={{ border: '1px solid rgba(0,0,0,0.08)' }}>
    <CardHeader title="Discipline Performance Radar" />
    <CardContent sx={{ display: 'flex', justifyContent: 'center' }}>
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={disciplines}>
          <PolarGrid stroke="rgba(0,0,0,0.1)" />
          <PolarAngleAxis dataKey="discipline" />
          <PolarRadiusAxis />
          <Radar
            name="Coordination Score"
            dataKey="coordinationScore"
            stroke="#8884d8"
            fill="#8884d8"
            fillOpacity={0.6}
          />
          <Radar
            name="Resolution Rate"
            dataKey="resolutionRate"
            stroke="#82ca9d"
            fill="#82ca9d"
            fillOpacity={0.6}
          />
          <ChartTooltip />
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
    </CardContent>
  </Card>
);

const QualityMatrixTable: React.FC<{ data: ElementQuality[] }> = ({ data }) => (
  <TableContainer component={Paper}>
    <Table>
      <TableHead sx={{ backgroundColor: '#f5f5f5' }}>
        <TableRow>
          <TableCell sx={{ fontWeight: 600 }}>Element Type</TableCell>
          <TableCell align="right" sx={{ fontWeight: 600 }}>
            Completeness
          </TableCell>
          <TableCell align="right" sx={{ fontWeight: 600 }}>
            Accuracy
          </TableCell>
          <TableCell align="right" sx={{ fontWeight: 600 }}>
            Parametrization
          </TableCell>
          <TableCell align="right" sx={{ fontWeight: 600 }}>
            Status</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {data.map((row) => (
          <TableRow key={row.type} hover>
            <TableCell sx={{ fontWeight: 500 }}>{row.type}</TableCell>
            <TableCell align="right">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={row.modelCompleteness}
                  sx={{ flex: 1, minWidth: 100 }}
                />
                <Typography variant="caption">{row.modelCompleteness}%</Typography>
              </Box>
            </TableCell>
            <TableCell align="right">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={row.dataAccuracy}
                  sx={{ flex: 1, minWidth: 100 }}
                  color={row.dataAccuracy >= 85 ? 'success' : 'warning'}
                />
                <Typography variant="caption">{row.dataAccuracy}%</Typography>
              </Box>
            </TableCell>
            <TableCell align="right">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={row.parametrization}
                  sx={{ flex: 1, minWidth: 100 }}
                  color={row.parametrization >= 80 ? 'success' : 'warning'}
                />
                <Typography variant="caption">{row.parametrization}%</Typography>
              </Box>
            </TableCell>
            <TableCell align="right">
              {row.modelCompleteness >= 90 && row.dataAccuracy >= 85 ? (
                <Chip
                  icon={<CheckCircleIcon />}
                  label="Good"
                  size="small"
                  color="success"
                  variant="outlined"
                />
              ) : (
                <Chip
                  icon={<ErrorIcon />}
                  label="Review"
                  size="small"
                  color="error"
                  variant="outlined"
                />
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </TableContainer>
);

const ProjectTimeline: React.FC<{ events: TimelineEvent[] }> = ({ events }) => (
  <Card sx={{ border: '1px solid rgba(0,0,0,0.08)' }}>
    <CardHeader title="Project Timeline" />
    <CardContent>
      <Timeline position="alternate">
        {events.map((event, index) => (
          <TimelineItem key={index}>
            <TimelineOppositeContent color="textSecondary" variant="caption">
              {event.date}
              {event.daysOverdue && (
                <Box sx={{ color: '#f44336', fontWeight: 600, fontSize: '0.85rem' }}>
                  {event.daysOverdue} days late
                </Box>
              )}
            </TimelineOppositeContent>
            <TimelineSeparator>
              <TimelineDot
                sx={{
                  backgroundColor:
                    event.status === 'completed'
                      ? '#4CAF50'
                      : event.status === 'in-progress'
                      ? '#2196F3'
                      : '#BDBDBD',
                }}
              >
                {event.status === 'completed' && <CheckCircleIcon />}
                {event.status === 'in-progress' && <AccessTimeIcon />}
              </TimelineDot>
              {index < events.length - 1 && <TimelineConnector />}
            </TimelineSeparator>
            <TimelineContent sx={{ py: '12px', px: 2 }}>
              <Typography variant="h6" component="span">
                {event.milestone}
              </Typography>
              <Typography variant="caption" display="block" color="textSecondary">
                {event.status}
              </Typography>
            </TimelineContent>
          </TimelineItem>
        ))}
      </Timeline>
    </CardContent>
  </Card>
);

const ClashTrendChart: React.FC<{ data: any[] }> = ({ data }) => (
  <Card sx={{ border: '1px solid rgba(0,0,0,0.08)' }}>
    <CardHeader title="Clash Detection Trends" subtitle="Critical vs Warnings" />
    <CardContent>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis stroke="rgba(0,0,0,0.5)" />
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
            dataKey="critical"
            fill="#f44336"
            stroke="#f44336"
            fillOpacity={0.2}
            name="Critical Clashes"
          />
          <Area
            type="monotone"
            dataKey="warnings"
            fill="#FF9800"
            stroke="#FF9800"
            fillOpacity={0.2}
            name="Warnings"
          />
          <Bar dataKey="resolved" fill="#4CAF50" name="Resolved" />
        </ComposedChart>
      </ResponsiveContainer>
    </CardContent>
  </Card>
);

const AnalyticsDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  // Sample data
  const disciplineData: DisciplinePerformance[] = [
    {
      discipline: 'Structural',
      coordinationScore: 85,
      clashCount: 12,
      resolutionRate: 92,
      trend: 5,
    },
    {
      discipline: 'MEP',
      coordinationScore: 78,
      clashCount: 28,
      resolutionRate: 85,
      trend: -3,
    },
    {
      discipline: 'Architectural',
      coordinationScore: 88,
      clashCount: 8,
      resolutionRate: 95,
      trend: 8,
    },
    {
      discipline: 'Civil',
      coordinationScore: 82,
      clashCount: 15,
      resolutionRate: 87,
      trend: 2,
    },
  ];

  const qualityData: ElementQuality[] = [
    { type: 'Structural Elements', modelCompleteness: 95, dataAccuracy: 92, parametrization: 88 },
    { type: 'MEP Systems', modelCompleteness: 82, dataAccuracy: 78, parametrization: 75 },
    { type: 'Architectural', modelCompleteness: 98, dataAccuracy: 95, parametrization: 92 },
    { type: 'Spaces', modelCompleteness: 90, dataAccuracy: 87, parametrization: 85 },
  ];

  const timelineEvents: TimelineEvent[] = [
    { date: 'Dec 1', milestone: 'Conceptual Review', status: 'completed' },
    { date: 'Dec 15', milestone: 'Schematic Phase', status: 'in-progress' },
    { date: 'Dec 28', milestone: 'Design Development', status: 'pending', daysOverdue: 0 },
    { date: 'Jan 15', milestone: 'Construction Documents', status: 'pending' },
  ];

  const clashData = [
    { date: 'Week 1', critical: 45, warnings: 120, resolved: 12 },
    { date: 'Week 2', critical: 38, warnings: 105, resolved: 28 },
    { date: 'Week 3', critical: 28, warnings: 92, resolved: 35 },
    { date: 'Week 4', critical: 18, warnings: 75, resolved: 42 },
  ];

  return (
    <Box sx={{ p: 3, background: '#f5f7fa', minHeight: '100vh' }}>
      {/* HEADER */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Analytics Dashboard
        </Typography>
        <Typography color="textSecondary">
          Deep dive into model quality, coordination, and project performance
        </Typography>
      </Box>

      {/* TIME RANGE SELECTOR */}
      <Box sx={{ mb: 4 }}>
        <ButtonGroup size="small" variant="outlined">
          <Button>1W</Button>
          <Button variant="contained">1M</Button>
          <Button>3M</Button>
          <Button>1Y</Button>
        </ButtonGroup>
      </Box>

      {/* MAIN CONTENT */}
      <Tabs
        value={tabValue}
        onChange={(e, newValue) => setTabValue(newValue)}
        sx={{ mb: 3, borderBottom: '1px solid rgba(0,0,0,0.1)' }}
      >
        <Tab label="Coordination & Clashes" id="tab-0" aria-controls="tabpanel-0" />
        <Tab label="Model Quality" id="tab-1" aria-controls="tabpanel-1" />
        <Tab label="Timeline & Milestones" id="tab-2" aria-controls="tabpanel-2" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <PerformanceRadar disciplines={disciplineData} />
          </Grid>
          <Grid item xs={12} md={6}>
            <ClashTrendChart data={clashData} />
          </Grid>
          <Grid item xs={12}>
            <Card sx={{ border: '1px solid rgba(0,0,0,0.08)' }}>
              <CardHeader title="Discipline Rankings" />
              <CardContent>
                <Grid container spacing={2}>
                  {disciplineData
                    .sort((a, b) => b.coordinationScore - a.coordinationScore)
                    .map((discipline, index) => (
                      <Grid item xs={12} sm={6} md={3} key={discipline.discipline}>
                        <Paper
                          sx={{
                            p: 2,
                            textAlign: 'center',
                            backgroundColor:
                              index === 0 ? '#E8F5E9' : index === 1 ? '#E3F2FD' : '#F5F5F5',
                          }}
                        >
                          <Typography
                            variant="h6"
                            sx={{
                              fontWeight: 700,
                              color: index === 0 ? '#1B5E20' : undefined,
                            }}
                          >
                            {index + 1}. {discipline.discipline}
                          </Typography>
                          <Box sx={{ mt: 2 }}>
                            <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
                              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                                {discipline.coordinationScore}
                              </Typography>
                              {discipline.trend > 0 ? (
                                <TrendingUpIcon sx={{ color: '#4CAF50' }} />
                              ) : (
                                <TrendingDownIcon sx={{ color: '#f44336' }} />
                              )}
                            </Box>
                            <Typography variant="caption" color="textSecondary">
                              Coordination Score
                            </Typography>
                          </Box>
                        </Paper>
                      </Grid>
                    ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Model Quality Assessment
            </Typography>
            <QualityMatrixTable data={qualityData} />
          </Grid>
          <Grid item xs={12}>
            <Card sx={{ border: '1px solid rgba(0,0,0,0.08)' }}>
              <CardHeader title="Quality Metrics Summary" />
              <CardContent>
                <Grid container spacing={3}>
                  {[
                    { label: 'Avg Completeness', value: '91%', trend: 3 },
                    { label: 'Avg Accuracy', value: '88%', trend: -2 },
                    { label: 'Avg Parametrization', value: '85%', trend: 5 },
                    { label: 'Model Standards Compliance', value: '87%', trend: 1 },
                  ].map((metric) => (
                    <Grid item xs={12} sm={6} md={3} key={metric.label}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="caption" color="textSecondary">
                          {metric.label}
                        </Typography>
                        <Typography variant="h5" sx={{ fontWeight: 700, mt: 1 }}>
                          {metric.value}
                        </Typography>
                        <Box display="flex" alignItems="center" justifyContent="center" gap={0.5} sx={{ mt: 1 }}>
                          {metric.trend > 0 ? (
                            <TrendingUpIcon sx={{ fontSize: '1rem', color: '#4CAF50' }} />
                          ) : (
                            <TrendingDownIcon sx={{ fontSize: '1rem', color: '#f44336' }} />
                          )}
                          <Typography
                            variant="caption"
                            sx={{
                              color: metric.trend > 0 ? '#4CAF50' : '#f44336',
                              fontWeight: 600,
                            }}
                          >
                            {Math.abs(metric.trend)}%
                          </Typography>
                        </Box>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <ProjectTimeline events={timelineEvents} />
          </Grid>
        </Grid>
      </TabPanel>
    </Box>
  );
};

export default AnalyticsDashboard;
// @ts-nocheck
