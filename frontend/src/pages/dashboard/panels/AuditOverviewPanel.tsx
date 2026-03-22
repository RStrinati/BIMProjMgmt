import { useMemo, useState } from 'react';
import {
  Grid,
  Stack,
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
import { ComplianceDonutCard } from '../components/ComplianceDonutCard';
import { ExceptionTableCard } from '../components/ExceptionTableCard';
import { ComparisonTableCard } from '../components/ComparisonTableCard';
import { KpiStrip } from '../KpiStrip';
import { DataFreshnessBadge } from '../DataFreshnessBadge';
import { LastRefreshStatus } from '../LastRefreshStatus';
import { formatDateTime, formatNumber } from '../utils';

export function AuditOverviewPanel() {
  const { filters } = useDashboardFilters();
  const { projectIds } = useDashboardProjectFilter();
  const [namingStatus, setNamingStatus] = useState<'all' | 'valid' | 'invalid' | 'unknown'>('invalid');
  const [coordPage, setCoordPage] = useState(1);
  const [coordPageSize, setCoordPageSize] = useState(25);

  const namingComplianceQuery = useQuery({
    queryKey: ['dashboard', 'naming-compliance', projectIds, filters.discipline],
    queryFn: () =>
      dashboardApi.getNamingCompliance({
        projectIds: projectIds.length ? projectIds : undefined,
        discipline: filters.discipline !== 'all' ? filters.discipline : undefined,
      }),
  });

  const namingTableQuery = useQuery({
    queryKey: ['dashboard', 'naming-compliance-table', projectIds, filters.discipline, namingStatus],
    queryFn: () =>
      dashboardApi.getNamingComplianceTable({
        projectIds: projectIds.length ? projectIds : undefined,
        discipline: filters.discipline !== 'all' ? filters.discipline : undefined,
        validationStatus: namingStatus !== 'all' ? namingStatus : undefined,
        page: 1,
        pageSize: 50,
      }),
  });

  const coordinateQuery = useQuery({
    queryKey: ['dashboard', 'coordinate-alignment', projectIds, filters.discipline, coordPage, coordPageSize],
    queryFn: () =>
      dashboardApi.getCoordinateAlignment({
        projectIds: projectIds.length ? projectIds : undefined,
        discipline: filters.discipline !== 'all' ? filters.discipline : undefined,
        page: coordPage,
        pageSize: coordPageSize,
        sortBy: 'model_file_name',
        sortDir: 'asc',
      }),
  });

  const namingSummary = namingComplianceQuery.data?.summary;
  const namingCompliancePct = namingSummary?.compliance_pct ?? 0;
  const namingValid = namingSummary?.valid_files ?? 0;
  const namingInvalid = namingSummary?.invalid_files ?? 0;

  const basePointStats = useMemo(() => {
    const modelRows = coordinateQuery.data?.model_base_points ?? [];
    let compliant = 0;
    let nonCompliant = 0;
    let unknown = 0;
    modelRows.forEach((row) => {
      const status = (row.pbp_compliance_status || '').toLowerCase();
      if (status.includes('compliant')) compliant += 1;
      else if (status.includes('non') || status.includes('fail')) nonCompliant += 1;
      else unknown += 1;
    });
    return { compliant, nonCompliant, unknown };
  }, [coordinateQuery.data]);

  const surveyPointStats = useMemo(() => {
    const modelRows = coordinateQuery.data?.model_survey_points ?? [];
    let compliant = 0;
    let nonCompliant = 0;
    let unknown = 0;
    modelRows.forEach((row) => {
      const status = (row.survey_compliance_status || '').toLowerCase();
      if (status.includes('compliant')) compliant += 1;
      else if (status.includes('non') || status.includes('fail')) nonCompliant += 1;
      else unknown += 1;
    });
    return { compliant, nonCompliant, unknown };
  }, [coordinateQuery.data]);

  const namingRows = namingTableQuery.data?.rows ?? [];
  const controlBasePoints = coordinateQuery.data?.control_base_points ?? [];
  const controlSurveyPoints = coordinateQuery.data?.control_survey_points ?? [];
  const modelBasePoints = coordinateQuery.data?.model_base_points ?? [];
  const modelSurveyPoints = coordinateQuery.data?.model_survey_points ?? [];

  return (
    <Stack spacing={3}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
        <Stack spacing={0.5}>
          <Typography variant="h4">Audit Overview</Typography>
          <Typography variant="body2" color="text.secondary">
            Compliance signals that match the underlying exception tables.
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center">
          <DataFreshnessBadge asOf={namingComplianceQuery.data?.as_of || coordinateQuery.data?.as_of} />
          <LastRefreshStatus updatedAt={namingComplianceQuery.dataUpdatedAt} />
        </Stack>
      </Stack>

      <KpiStrip
        items={[
          {
            label: 'File Naming Compliance',
            value: `${Math.round(namingCompliancePct)}%`,
            helper: `${formatNumber(namingValid)} compliant`,
          },
          {
            label: 'Project Base Point Compliance',
            value: `${Math.round(
              basePointStats.compliant + basePointStats.nonCompliant + basePointStats.unknown === 0
                ? 0
                : (basePointStats.compliant /
                    (basePointStats.compliant + basePointStats.nonCompliant + basePointStats.unknown)) *
                  100,
            )}%`,
            helper: `${formatNumber(basePointStats.nonCompliant)} non-compliant`,
          },
          {
            label: 'Survey Point Compliance',
            value: `${Math.round(
              surveyPointStats.compliant + surveyPointStats.nonCompliant + surveyPointStats.unknown === 0
                ? 0
                : (surveyPointStats.compliant /
                    (surveyPointStats.compliant + surveyPointStats.nonCompliant + surveyPointStats.unknown)) *
                  100,
            )}%`,
            helper: `${formatNumber(surveyPointStats.nonCompliant)} non-compliant`,
          },
          {
            label: 'Latest Validation',
            value: namingSummary?.latest_validated ? formatDateTime(namingSummary.latest_validated) : '--',
            helper: `${formatNumber(namingSummary?.total_files)} files checked`,
          },
        ]}
      />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <ComplianceDonutCard
            title="File Naming Compliance"
            compliant={namingValid}
            nonCompliant={namingInvalid}
            onClickSegment={(segment) => {
              if (segment === 'compliant') setNamingStatus('valid');
              if (segment === 'non_compliant') setNamingStatus('invalid');
              if (segment === 'unknown') setNamingStatus('unknown');
            }}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <ComplianceDonutCard
            title="Project Base Point Compliance"
            compliant={basePointStats.compliant}
            nonCompliant={basePointStats.nonCompliant}
            unknown={basePointStats.unknown}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <ComplianceDonutCard
            title="Survey Point Compliance"
            compliant={surveyPointStats.compliant}
            nonCompliant={surveyPointStats.nonCompliant}
            unknown={surveyPointStats.unknown}
          />
        </Grid>

        <Grid item xs={12}>
          <ExceptionTableCard
            title="File Naming Exceptions"
            subtitle="Failures appear here first. Click the donut to filter the table."
          >
            <TableContainer>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Project</TableCell>
                    <TableCell>File Name</TableCell>
                    <TableCell>Discipline</TableCell>
                    <TableCell>Validation Status</TableCell>
                    <TableCell>Failed Field Value</TableCell>
                    <TableCell>Failure Reason</TableCell>
                    <TableCell>Validated</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {namingRows.map((row, idx) => (
                    <TableRow key={`${row.model_file_name}-${idx}`}>
                      <TableCell>{row.project_name ?? '--'}</TableCell>
                      <TableCell>{row.model_file_name ?? '--'}</TableCell>
                      <TableCell>{row.discipline ?? '--'}</TableCell>
                      <TableCell>{row.validation_status ?? '--'}</TableCell>
                      <TableCell>{row.failed_field_value ?? '--'}</TableCell>
                      <TableCell>{row.failed_field_reason ?? '--'}</TableCell>
                      <TableCell>{formatDateTime(row.validated_date)}</TableCell>
                    </TableRow>
                  ))}
                  {!namingRows.length && (
                    <TableRow>
                      <TableCell colSpan={7}>
                        <Typography variant="body2" color="text.secondary">
                          No naming exceptions found for the current filters.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </ExceptionTableCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <ComparisonTableCard title="Control Project Base Point" subtitle="Reference control model values">
            <TableContainer>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Control File</TableCell>
                    <TableCell>Zone</TableCell>
                    <TableCell align="right">PBP EW</TableCell>
                    <TableCell align="right">PBP NS</TableCell>
                    <TableCell align="right">PBP Elev</TableCell>
                    <TableCell align="right">Angle</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {controlBasePoints.map((row, idx) => (
                    <TableRow key={`${row.control_file_name}-${idx}`}>
                      <TableCell>{row.control_file_name ?? '--'}</TableCell>
                      <TableCell>{row.control_zone_code ?? '--'}</TableCell>
                      <TableCell align="right">{row.control_pbp_eastwest ?? '--'}</TableCell>
                      <TableCell align="right">{row.control_pbp_northsouth ?? '--'}</TableCell>
                      <TableCell align="right">{row.control_pbp_elevation ?? '--'}</TableCell>
                      <TableCell align="right">{row.control_pbp_angle_true_north ?? '--'}</TableCell>
                    </TableRow>
                  ))}
                  {!controlBasePoints.length && (
                    <TableRow>
                      <TableCell colSpan={6}>
                        <Typography variant="body2" color="text.secondary">
                          No control base point records available.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </ComparisonTableCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <ComparisonTableCard title="Control Project Survey Point" subtitle="Reference survey point values">
            <TableContainer>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Control File</TableCell>
                    <TableCell>Zone</TableCell>
                    <TableCell align="right">Survey EW</TableCell>
                    <TableCell align="right">Survey NS</TableCell>
                    <TableCell align="right">Survey Elev</TableCell>
                    <TableCell align="right">Angle</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {controlSurveyPoints.map((row, idx) => (
                    <TableRow key={`${row.control_file_name}-${idx}`}>
                      <TableCell>{row.control_file_name ?? '--'}</TableCell>
                      <TableCell>{row.control_zone_code ?? '--'}</TableCell>
                      <TableCell align="right">{row.control_survey_eastwest ?? '--'}</TableCell>
                      <TableCell align="right">{row.control_survey_northsouth ?? '--'}</TableCell>
                      <TableCell align="right">{row.control_survey_elevation ?? '--'}</TableCell>
                      <TableCell align="right">{row.control_survey_angle_true_north ?? '--'}</TableCell>
                    </TableRow>
                  ))}
                  {!controlSurveyPoints.length && (
                    <TableRow>
                      <TableCell colSpan={6}>
                        <Typography variant="body2" color="text.secondary">
                          No control survey point records available.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </ComparisonTableCard>
        </Grid>

        <Grid item xs={12}>
          <ComparisonTableCard title="Model Project Base Point Comparison" subtitle="Model vs control base points">
            <TableContainer>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Model File</TableCell>
                    <TableCell>Discipline</TableCell>
                    <TableCell>Zone</TableCell>
                    <TableCell>Control File</TableCell>
                    <TableCell align="right">PBP EW</TableCell>
                    <TableCell align="right">PBP NS</TableCell>
                    <TableCell align="right">PBP Elev</TableCell>
                    <TableCell align="right">Angle</TableCell>
                    <TableCell>Compliance</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {modelBasePoints.map((row, idx) => (
                    <TableRow key={`${row.model_file_name}-${idx}`}>
                      <TableCell>{row.model_file_name ?? '--'}</TableCell>
                      <TableCell>{row.discipline ?? '--'}</TableCell>
                      <TableCell>{row.model_zone_code ?? '--'}</TableCell>
                      <TableCell>{row.control_file_name ?? '--'}</TableCell>
                      <TableCell align="right">{row.pbp_eastwest ?? '--'}</TableCell>
                      <TableCell align="right">{row.pbp_northsouth ?? '--'}</TableCell>
                      <TableCell align="right">{row.pbp_elevation ?? '--'}</TableCell>
                      <TableCell align="right">{row.pbp_angle_true_north ?? '--'}</TableCell>
                      <TableCell>{row.pbp_compliance_status ?? '--'}</TableCell>
                    </TableRow>
                  ))}
                  {!modelBasePoints.length && (
                    <TableRow>
                      <TableCell colSpan={9}>
                        <Typography variant="body2" color="text.secondary">
                          No model base point data available.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </ComparisonTableCard>
        </Grid>

        <Grid item xs={12}>
          <ComparisonTableCard title="Model Project Survey Point Comparison" subtitle="Model vs control survey points">
            <TableContainer>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Model File</TableCell>
                    <TableCell>Discipline</TableCell>
                    <TableCell>Zone</TableCell>
                    <TableCell>Control File</TableCell>
                    <TableCell align="right">Survey EW</TableCell>
                    <TableCell align="right">Survey NS</TableCell>
                    <TableCell align="right">Survey Elev</TableCell>
                    <TableCell align="right">Angle</TableCell>
                    <TableCell>Compliance</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {modelSurveyPoints.map((row, idx) => (
                    <TableRow key={`${row.model_file_name}-${idx}`}>
                      <TableCell>{row.model_file_name ?? '--'}</TableCell>
                      <TableCell>{row.discipline ?? '--'}</TableCell>
                      <TableCell>{row.model_zone_code ?? '--'}</TableCell>
                      <TableCell>{row.control_file_name ?? '--'}</TableCell>
                      <TableCell align="right">{row.survey_eastwest ?? '--'}</TableCell>
                      <TableCell align="right">{row.survey_northsouth ?? '--'}</TableCell>
                      <TableCell align="right">{row.survey_elevation ?? '--'}</TableCell>
                      <TableCell align="right">{row.survey_angle_true_north ?? '--'}</TableCell>
                      <TableCell>{row.survey_compliance_status ?? '--'}</TableCell>
                    </TableRow>
                  ))}
                  {!modelSurveyPoints.length && (
                    <TableRow>
                      <TableCell colSpan={9}>
                        <Typography variant="body2" color="text.secondary">
                          No model survey point data available.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              component="div"
              count={coordinateQuery.data?.total ?? 0}
              page={Math.max(coordPage - 1, 0)}
              onPageChange={(_, page) => setCoordPage(page + 1)}
              rowsPerPage={coordPageSize}
              onRowsPerPageChange={(event) => {
                const next = parseInt(event.target.value, 10);
                setCoordPageSize(Number.isNaN(next) ? 25 : next);
                setCoordPage(1);
              }}
              rowsPerPageOptions={[10, 25, 50]}
            />
          </ComparisonTableCard>
        </Grid>
      </Grid>
    </Stack>
  );
}
