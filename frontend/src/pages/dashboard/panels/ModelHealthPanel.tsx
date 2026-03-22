import { useState } from 'react';
import {
  Grid,
  Stack,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/api/dashboard';
import { useDashboardFilters } from '../DashboardFiltersContext';
import { useDashboardProjectFilter } from '../useDashboardProjectFilter';
import { SummaryCard } from '../components/SummaryCard';
import { ExceptionTableCard } from '../components/ExceptionTableCard';
import { DataFreshnessBadge } from '../DataFreshnessBadge';
import { LastRefreshStatus } from '../LastRefreshStatus';
import { formatDateTime } from '../utils';

export function ModelHealthPanel() {
  const { filters } = useDashboardFilters();
  const { projectIds } = useDashboardProjectFilter();
  const [tab, setTab] = useState(0);
  const [gridPage, setGridPage] = useState(1);
  const [gridPageSize, setGridPageSize] = useState(25);
  const [levelPage, setLevelPage] = useState(1);
  const [levelPageSize, setLevelPageSize] = useState(25);

  const namingQuery = useQuery({
    queryKey: ['dashboard', 'naming-compliance', projectIds, filters.discipline],
    queryFn: () =>
      dashboardApi.getNamingCompliance({
        projectIds: projectIds.length ? projectIds : undefined,
        discipline: filters.discipline !== 'all' ? filters.discipline : undefined,
      }),
  });

  const namingTableQuery = useQuery({
    queryKey: ['dashboard', 'naming-compliance-table', projectIds, filters.discipline],
    queryFn: () =>
      dashboardApi.getNamingComplianceTable({
        projectIds: projectIds.length ? projectIds : undefined,
        discipline: filters.discipline !== 'all' ? filters.discipline : undefined,
        validationStatus: 'invalid',
        page: 1,
        pageSize: 50,
      }),
  });

  const coordQuery = useQuery({
    queryKey: ['dashboard', 'coordinate-alignment', projectIds, filters.discipline],
    queryFn: () =>
      dashboardApi.getCoordinateAlignment({
        projectIds: projectIds.length ? projectIds : undefined,
        discipline: filters.discipline !== 'all' ? filters.discipline : undefined,
        page: 1,
        pageSize: 50,
      }),
  });

  const gridQuery = useQuery({
    queryKey: ['dashboard', 'health-grids', projectIds, filters.discipline, gridPage, gridPageSize],
    queryFn: () =>
      dashboardApi.getGridAlignment({
        projectIds: projectIds.length ? projectIds : undefined,
        discipline: filters.discipline !== 'all' ? filters.discipline : undefined,
        page: gridPage,
        pageSize: gridPageSize,
        sortBy: 'project_name',
        sortDir: 'asc',
      }),
  });

  const levelQuery = useQuery({
    queryKey: ['dashboard', 'health-levels', projectIds, filters.discipline, levelPage, levelPageSize],
    queryFn: () =>
      dashboardApi.getLevelAlignment({
        projectIds: projectIds.length ? projectIds : undefined,
        discipline: filters.discipline !== 'all' ? filters.discipline : undefined,
        toleranceMm: 5,
        page: levelPage,
        pageSize: levelPageSize,
        sortBy: 'project_name',
        sortDir: 'asc',
      }),
  });

  const namingSummary = namingQuery.data?.summary;

  return (
    <Stack spacing={3}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
        <Stack spacing={0.5}>
          <Typography variant="h4">Model Health</Typography>
          <Typography variant="body2" color="text.secondary">
            Diagnostics focused on exceptions and misalignments.
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center">
          <DataFreshnessBadge asOf={namingQuery.data?.as_of || gridQuery.data?.as_of} />
          <LastRefreshStatus updatedAt={namingQuery.dataUpdatedAt} />
        </Stack>
      </Stack>

      <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <SummaryCard
            label="Naming Failures"
            value={namingSummary?.invalid_files ?? 0}
            helper={`${namingSummary?.total_files ?? 0} total files`}
            accent="error.main"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <SummaryCard
            label="Coordinate Exceptions"
            value={(coordQuery.data?.model_base_points ?? []).length}
            helper="Models flagged for review"
            accent="warning.main"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <SummaryCard
            label="Grid Deviations"
            value={gridQuery.data?.total ?? 0}
            helper="Alignment checks"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <SummaryCard
            label="Level Deviations"
            value={levelQuery.data?.total ?? 0}
            helper="Tolerance breaches"
          />
        </Grid>
      </Grid>

      <Tabs value={tab} onChange={(_, next) => setTab(next)}>
        <Tab label="Naming" />
        <Tab label="Coordinates" />
        <Tab label="Grids" />
        <Tab label="Levels" />
      </Tabs>

      {tab === 0 && (
        <ExceptionTableCard title="Naming Exceptions" subtitle="Only invalid files shown">
          <TableContainer>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Project</TableCell>
                  <TableCell>File Name</TableCell>
                  <TableCell>Discipline</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell>Validated</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(namingTableQuery.data?.rows ?? []).map((row, idx) => (
                  <TableRow key={`${row.model_file_name}-${idx}`}>
                    <TableCell>{row.project_name ?? '--'}</TableCell>
                    <TableCell>{row.model_file_name ?? '--'}</TableCell>
                    <TableCell>{row.discipline ?? '--'}</TableCell>
                    <TableCell>{row.validation_status ?? '--'}</TableCell>
                    <TableCell>{row.failed_field_reason ?? '--'}</TableCell>
                    <TableCell>{formatDateTime(row.validated_date)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </ExceptionTableCard>
      )}

      {tab === 1 && (
        <ExceptionTableCard title="Coordinate Exceptions" subtitle="Models failing base or survey point checks">
          <TableContainer>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Model File</TableCell>
                  <TableCell>Discipline</TableCell>
                  <TableCell>Zone</TableCell>
                  <TableCell>Base Point</TableCell>
                  <TableCell>Survey Point</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(coordQuery.data?.model_base_points ?? []).map((row, idx) => (
                  <TableRow key={`${row.model_file_name}-${idx}`}>
                    <TableCell>{row.model_file_name ?? '--'}</TableCell>
                    <TableCell>{row.discipline ?? '--'}</TableCell>
                    <TableCell>{row.model_zone_code ?? '--'}</TableCell>
                    <TableCell>{row.pbp_compliance_status ?? '--'}</TableCell>
                    <TableCell>{row.survey_compliance_status ?? '--'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </ExceptionTableCard>
      )}

      {tab === 2 && (
        <ExceptionTableCard title="Grid Alignment" subtitle="Misaligned grids and deviations">
          <TableContainer>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Project</TableCell>
                  <TableCell>Model File</TableCell>
                  <TableCell>Grid</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Alignment</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(gridQuery.data?.items ?? []).map((row, idx) => (
                  <TableRow key={`${row.model_file_name}-${row.grid_name}-${idx}`}>
                    <TableCell>{row.project_name ?? '--'}</TableCell>
                    <TableCell>{row.model_file_name ?? '--'}</TableCell>
                    <TableCell>{row.grid_name ?? '--'}</TableCell>
                    <TableCell>{row.status_flag ?? '--'}</TableCell>
                    <TableCell>{row.alignment_status ?? '--'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={gridQuery.data?.total ?? 0}
            page={Math.max(gridPage - 1, 0)}
            onPageChange={(_, next) => setGridPage(next + 1)}
            rowsPerPage={gridPageSize}
            onRowsPerPageChange={(event) => {
              const next = parseInt(event.target.value, 10);
              setGridPageSize(Number.isNaN(next) ? 25 : next);
              setGridPage(1);
            }}
            rowsPerPageOptions={[10, 25, 50]}
          />
        </ExceptionTableCard>
      )}

      {tab === 3 && (
        <ExceptionTableCard title="Level Alignment" subtitle="Level differences beyond tolerance">
          <TableContainer>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Project</TableCell>
                  <TableCell>Model File</TableCell>
                  <TableCell>Level</TableCell>
                  <TableCell>Diff (mm)</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(levelQuery.data?.items ?? []).map((row, idx) => (
                  <TableRow key={`${row.model_file_name}-${row.model_level_name}-${idx}`}>
                    <TableCell>{row.project_name ?? '--'}</TableCell>
                    <TableCell>{row.model_file_name ?? '--'}</TableCell>
                    <TableCell>{row.model_level_name ?? '--'}</TableCell>
                    <TableCell>{row.elevation_diff_mm ?? '--'}</TableCell>
                    <TableCell>{row.alignment_status ?? '--'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={levelQuery.data?.total ?? 0}
            page={Math.max(levelPage - 1, 0)}
            onPageChange={(_, next) => setLevelPage(next + 1)}
            rowsPerPage={levelPageSize}
            onRowsPerPageChange={(event) => {
              const next = parseInt(event.target.value, 10);
              setLevelPageSize(Number.isNaN(next) ? 25 : next);
              setLevelPage(1);
            }}
            rowsPerPageOptions={[10, 25, 50]}
          />
        </ExceptionTableCard>
      )}
    </Stack>
  );
}
