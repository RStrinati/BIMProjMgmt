
import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Checkbox,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { bidsApi, clientsApi, projectsApi, usersApi } from '@/api';
import type {
  Bid,
  BidSection,
  BidScopeItem,
  BidScopeTemplate,
  BidProgramStage,
  BidBillingLine,
  BidAwardResult,
  Client,
  Project,
  User,
} from '@/types/api';

const BID_STATUSES = ['DRAFT', 'SUBMITTED', 'AWARDED', 'LOST', 'ARCHIVED'];
const BID_TYPES = ['PROPOSAL', 'FEE_UPDATE', 'VARIATION'];
const PROGRAM_CADENCES = ['weekly', 'fortnightly', 'monthly'];
const EXCLUSION_KEYWORDS = ['o&m', 'asset', 'validation'];

const emptyScopeItem: Partial<BidScopeItem> = {
  title: '',
  description: '',
  stage_name: '',
  included_qty: undefined,
  unit: '',
  unit_rate: undefined,
  lump_sum: undefined,
  is_optional: false,
};

const emptyProgramStage: Partial<BidProgramStage> = {
  stage_name: '',
  cadence: 'weekly',
  cycles_planned: 1,
};

const emptyBillingLine: Partial<BidBillingLine> = {
  period_start: '',
  period_end: '',
  amount: 0,
};

const getSectionText = (section?: BidSection): string => {
  if (!section?.content_json) {
    return '';
  }
  if (typeof section.content_json === 'string') {
    try {
      const parsed = JSON.parse(section.content_json);
      if (Array.isArray(parsed?.items)) {
        return parsed.items.join('\n');
      }
      if (typeof parsed?.text === 'string') {
        return parsed.text;
      }
    } catch {
      return section.content_json;
    }
    return section.content_json;
  }
  if (Array.isArray((section.content_json as any).items)) {
    return (section.content_json as any).items.join('\n');
  }
  if (typeof (section.content_json as any).text === 'string') {
    return (section.content_json as any).text;
  }
  return '';
};

const buildSectionPayload = (section_key: string, text: string, sort_order: number) => ({
  section_key,
  content_json: {
    items: text
      .split('\n')
      .map((item) => item.trim())
      .filter(Boolean),
  },
  sort_order,
});

const parseLines = (text: string) =>
  text
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean);

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(value || 0);

export default function BidDetailPage() {
  const { id } = useParams();
  const bidId = Number(id);
  const queryClient = useQueryClient();
  const [tab, setTab] = useState(0);
  const [overviewState, setOverviewState] = useState<Partial<Bid>>({});
  const [overviewMessage, setOverviewMessage] = useState<string | null>(null);

  const [scopeForm, setScopeForm] = useState<Partial<BidScopeItem>>(emptyScopeItem);
  const [scopeError, setScopeError] = useState<string | null>(null);
  const [selectedScopeTemplate, setSelectedScopeTemplate] = useState('');
  const [replaceScopeItems, setReplaceScopeItems] = useState(false);
  const [templateApplyError, setTemplateApplyError] = useState<string | null>(null);

  const [programDialogOpen, setProgramDialogOpen] = useState(false);
  const [programForm, setProgramForm] = useState<Partial<BidProgramStage>>(emptyProgramStage);
  const [programError, setProgramError] = useState<string | null>(null);

  const [billingDialogOpen, setBillingDialogOpen] = useState(false);
  const [billingForm, setBillingForm] = useState<Partial<BidBillingLine>>(emptyBillingLine);
  const [billingError, setBillingError] = useState<string | null>(null);

  const [assumptionsText, setAssumptionsText] = useState('');
  const [exclusionsText, setExclusionsText] = useState('');
  const [methodologyText, setMethodologyText] = useState('');
  const [optionsText, setOptionsText] = useState('');
  const [sectionsMessage, setSectionsMessage] = useState<string | null>(null);
  const [sectionsExpanded, setSectionsExpanded] = useState({
    assumptions: false,
    exclusions: false,
    methodology: false,
    options: false,
  });
  const [readinessDialogOpen, setReadinessDialogOpen] = useState(false);

  const [awardMessage, setAwardMessage] = useState<string | null>(null);
  const [awardError, setAwardError] = useState<string | null>(null);
  const [awardResult, setAwardResult] = useState<BidAwardResult | null>(null);
  const [createNewProject, setCreateNewProject] = useState(true);
  const [awardProjectId, setAwardProjectId] = useState<number | ''>('');
  const [newProjectPayload, setNewProjectPayload] = useState({
    project_name: '',
    status: 'Active',
  });

  const { data: schema } = useQuery({
    queryKey: ['schema-health'],
    queryFn: () => bidsApi.getSchemaHealth(),
    retry: 1,
    refetchOnWindowFocus: false,
    staleTime: 60 * 1000,
  });
  const schemaReady = schema?.bid_module_ready !== false;

  const { data: bid } = useQuery({
    queryKey: ['bid', bidId],
    queryFn: () => bidsApi.get(bidId),
    enabled: schemaReady && Number.isFinite(bidId),
  });

  const { data: sections } = useQuery({
    queryKey: ['bid', bidId, 'sections'],
    queryFn: () => bidsApi.getSections(bidId),
    enabled: schemaReady && Number.isFinite(bidId),
  });

  const { data: scopeItems } = useQuery({
    queryKey: ['bid', bidId, 'scope-items'],
    queryFn: () => bidsApi.listScopeItems(bidId),
    enabled: schemaReady && Number.isFinite(bidId),
  });

  const { data: scopeTemplates } = useQuery<BidScopeTemplate[]>({
    queryKey: ['bid-scope-templates'],
    queryFn: () => bidsApi.getScopeTemplates(),
  });

  const { data: programStages } = useQuery({
    queryKey: ['bid', bidId, 'program-stages'],
    queryFn: () => bidsApi.listProgramStages(bidId),
    enabled: schemaReady && Number.isFinite(bidId),
  });

  const { data: billingSchedule } = useQuery({
    queryKey: ['bid', bidId, 'billing-schedule'],
    queryFn: () => bidsApi.listBillingSchedule(bidId),
    enabled: schemaReady && Number.isFinite(bidId),
  });

  const { data: clients } = useQuery<Client[]>({
    queryKey: ['clients'],
    queryFn: () => clientsApi.getAll(),
  });

  const { data: projects } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: () => projectsApi.getAll(),
  });

  const { data: users } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll(),
  });

  useEffect(() => {
    if (bid) {
      setOverviewState({
        bid_name: bid.bid_name,
        bid_type: bid.bid_type,
        status: bid.status,
        probability: bid.probability ?? undefined,
        client_id: bid.client_id ?? undefined,
        project_id: bid.project_id ?? undefined,
        owner_user_id: bid.owner_user_id ?? undefined,
        currency_code: bid.currency_code ?? 'AUD',
        stage_framework: bid.stage_framework ?? 'CUSTOM',
        validity_days: bid.validity_days ?? undefined,
        gst_included: bid.gst_included ?? true,
        pi_notes: bid.pi_notes ?? '',
      });
    }
  }, [bid]);

  useEffect(() => {
    if (sections) {
      const assumptions = sections.find((section) => section.section_key === 'ASSUMPTIONS');
      const exclusions = sections.find((section) => section.section_key === 'EXCLUSIONS');
      const methodology = sections.find((section) => section.section_key === 'METHODOLOGY');
      const options = sections.find((section) => section.section_key === 'OPTIONS');
      setAssumptionsText(getSectionText(assumptions));
      setExclusionsText(getSectionText(exclusions));
      setMethodologyText(getSectionText(methodology));
      setOptionsText(getSectionText(options));
    }
  }, [sections]);
  const scopeTotals = useMemo(() => {
    let totalLumpSum = 0;
    let totalUnitValue = 0;
    let baseTotal = 0;
    let optionalTotal = 0;
    (scopeItems ?? []).forEach((item) => {
      const lumpSum = Number(item.lump_sum || 0);
      const unitValue = Number(item.unit_rate || 0) * Number(item.included_qty || 0);
      totalLumpSum += lumpSum;
      totalUnitValue += unitValue;
      const lineTotal = lumpSum + unitValue;
      if (item.is_optional) {
        optionalTotal += lineTotal;
      } else {
        baseTotal += lineTotal;
      }
    });
    return {
      totalLumpSum,
      totalUnitValue,
      baseTotal,
      optionalTotal,
      total: baseTotal + optionalTotal,
    };
  }, [scopeItems]);

  const billingTotal = useMemo(
    () => (billingSchedule ?? []).reduce((sum, line) => sum + Number(line.amount || 0), 0),
    [billingSchedule],
  );
  const billingPeriods = billingSchedule?.length ?? 0;
  const billingAverage = billingPeriods > 0 ? billingTotal / billingPeriods : 0;
  const servicesCount = scopeItems?.length ?? 0;
  const plannedReviewCycles = (programStages ?? []).reduce(
    (sum, stage) => sum + Number(stage.cycles_planned || 0),
    0,
  );
  const assumptionCount = parseLines(assumptionsText).length;
  const exclusionCount = parseLines(exclusionsText).length;
  const methodologyCount = parseLines(methodologyText).length;
  const optionsCount = parseLines(optionsText).length;

  useEffect(() => {
    const hasExclusionKeyword = EXCLUSION_KEYWORDS.some((keyword) =>
      exclusionsText.toLowerCase().includes(keyword),
    );
    setSectionsExpanded((prev) => ({
      assumptions: prev.assumptions || assumptionCount > 0,
      exclusions: prev.exclusions || exclusionCount > 0 || hasExclusionKeyword,
      methodology: prev.methodology || methodologyCount > 0,
      options: prev.options || optionsCount > 0,
    }));
  }, [assumptionsText, exclusionCount, exclusionsText, methodologyCount, optionsCount, assumptionCount]);

  const readinessChecks = useMemo(
    () => [
      { key: 'scope', label: 'At least 1 service', ok: servicesCount > 0 },
      { key: 'billing', label: 'At least 1 billing line', ok: billingPeriods > 0 },
      { key: 'fee', label: 'Total fee is greater than 0', ok: scopeTotals.total > 0 },
      { key: 'status', label: 'Bid not archived', ok: (bid?.status || '').toUpperCase() !== 'ARCHIVED' },
      { key: 'program', label: 'At least 1 program stage', ok: (programStages ?? []).length > 0 },
    ],
    [servicesCount, billingPeriods, scopeTotals.total, bid?.status, programStages],
  );
  const readinessScore = Math.round(
    (readinessChecks.filter((check) => check.ok).length / readinessChecks.length) * 100,
  );
  const readinessMissing = readinessChecks.filter((check) => !check.ok).map((check) => check.label);
  const clientName = clients?.find((client) => client.client_id === overviewState.client_id)?.client_name;
  const ownerName = users?.find((user) => user.user_id === overviewState.owner_user_id)?.name;

  const handleSaveOverview = async () => {
    setOverviewMessage(null);
    try {
      await bidsApi.update(bidId, overviewState);
      queryClient.invalidateQueries({ queryKey: ['bid', bidId] });
      setOverviewMessage('Overview updated.');
    } catch (err: any) {
      setOverviewMessage(err?.response?.data?.error || 'Failed to update bid.');
    }
  };

  const handleSaveSections = async () => {
    setSectionsMessage(null);
    try {
      const payload = [
        buildSectionPayload('ASSUMPTIONS', assumptionsText, 1),
        buildSectionPayload('EXCLUSIONS', exclusionsText, 2),
        buildSectionPayload('METHODOLOGY', methodologyText, 3),
        buildSectionPayload('OPTIONS', optionsText, 4),
      ];
      await bidsApi.updateSections(bidId, payload as BidSection[]);
      queryClient.invalidateQueries({ queryKey: ['bid', bidId, 'sections'] });
      setSectionsMessage('Sections updated.');
    } catch (err: any) {
      setSectionsMessage(err?.response?.data?.error || 'Failed to update sections.');
    }
  };

  const selectScopeItem = (item?: BidScopeItem) => {
    setScopeForm(item ? { ...item } : { ...emptyScopeItem });
    setScopeError(null);
  };

  const saveScopeItem = async () => {
    if (!scopeForm.title || scopeForm.title.trim() === '') {
      setScopeError('Title is required.');
      return;
    }
    try {
      if (scopeForm.scope_item_id) {
        await bidsApi.updateScopeItem(bidId, scopeForm.scope_item_id, scopeForm);
      } else {
        await bidsApi.createScopeItem(bidId, scopeForm);
      }
      queryClient.invalidateQueries({ queryKey: ['bid', bidId, 'scope-items'] });
    } catch (err: any) {
      setScopeError(err?.response?.data?.error || 'Failed to save scope item.');
    }
  };

  const clearScopeSelection = () => {
    setScopeForm({ ...emptyScopeItem });
    setScopeError(null);
  };

  const applyScopeTemplate = async () => {
    if (!selectedScopeTemplate) {
      setTemplateApplyError('Select a scope template before applying.');
      return;
    }
    setTemplateApplyError(null);
    try {
      await bidsApi.importScopeTemplate(bidId, {
        template_name: selectedScopeTemplate,
        replace_existing: replaceScopeItems,
      });
      queryClient.invalidateQueries({ queryKey: ['bid', bidId, 'scope-items'] });
    } catch (err: any) {
      setTemplateApplyError(err?.response?.data?.error || 'Failed to apply scope template.');
    }
  };

  const openProgramDialog = (stage?: BidProgramStage) => {
    setProgramForm(stage ? { ...stage } : { ...emptyProgramStage });
    setProgramError(null);
    setProgramDialogOpen(true);
  };

  const saveProgramStage = async () => {
    if (!programForm.stage_name || programForm.stage_name.trim() === '') {
      setProgramError('Stage name is required.');
      return;
    }
    try {
      if (programForm.program_stage_id) {
        await bidsApi.updateProgramStage(bidId, programForm.program_stage_id, programForm);
      } else {
        await bidsApi.createProgramStage(bidId, programForm);
      }
      setProgramDialogOpen(false);
      queryClient.invalidateQueries({ queryKey: ['bid', bidId, 'program-stages'] });
    } catch (err: any) {
      setProgramError(err?.response?.data?.error || 'Failed to save program stage.');
    }
  };

  const openBillingDialog = (line?: BidBillingLine) => {
    setBillingForm(line ? { ...line } : { ...emptyBillingLine });
    setBillingError(null);
    setBillingDialogOpen(true);
  };

  const saveBillingLine = async () => {
    if (!billingForm.period_start || !billingForm.period_end) {
      setBillingError('Period start and end are required.');
      return;
    }
    try {
      if (billingForm.billing_line_id) {
        await bidsApi.updateBillingLine(bidId, billingForm.billing_line_id, billingForm);
      } else {
        await bidsApi.createBillingLine(bidId, billingForm);
      }
      setBillingDialogOpen(false);
      queryClient.invalidateQueries({ queryKey: ['bid', bidId, 'billing-schedule'] });
    } catch (err: any) {
      setBillingError(err?.response?.data?.error || 'Failed to save billing line.');
    }
  };

  const handleAward = async () => {
    setAwardMessage(null);
    setAwardError(null);
    try {
      const payload = createNewProject
        ? { create_new_project: true, project_payload: newProjectPayload }
        : { create_new_project: false, project_id: awardProjectId || undefined };
      const result = await bidsApi.award(bidId, payload);
      setAwardResult(result);
      setAwardMessage('Bid converted successfully.');
      queryClient.invalidateQueries({ queryKey: ['bid', bidId] });
    } catch (err: any) {
      setAwardError(err?.response?.data?.error || 'Failed to award bid.');
    }
  };

  if (schema && !schemaReady) {
    return (
      <Box>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
          Bid workspace
        </Typography>
        <Alert severity="warning">
          Module not enabled - pending DB migration. Please run the Bid Management DBA Migration Pack.
        </Alert>
      </Box>
    );
  }

  const displayName = overviewState.bid_name || bid?.bid_name || 'Untitled bid';
  const displayType = overviewState.bid_type || bid?.bid_type || 'PROPOSAL';
  const displayStatus = overviewState.status || bid?.status || 'DRAFT';
  const displayProbability = overviewState.probability ?? bid?.probability ?? null;
  const displayFramework = overviewState.stage_framework || bid?.stage_framework || 'CUSTOM';

  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', md: '280px 1fr' },
        gap: 3,
        alignItems: 'start',
      }}
    >
      <Paper
        variant="outlined"
        sx={{
          p: 2,
          position: { md: 'sticky' },
          top: { md: 88 },
          alignSelf: 'start',
        }}
      >
        <Stack spacing={2}>
          <Stack spacing={0.5}>
            <Typography variant="overline" color="text.secondary">
              Bid overview
            </Typography>
            <Typography variant="h6">{displayName}</Typography>
            <Typography color="text.secondary">{clientName || bid?.client_name || 'Unassigned client'}</Typography>
          </Stack>

          <Stack spacing={0.5}>
            <Typography variant="subtitle2">Status</Typography>
            <Typography>{displayStatus}</Typography>
            {displayProbability !== null && <Typography color="text.secondary">{displayProbability}% probability</Typography>}
            <Typography color="text.secondary">Type: {displayType}</Typography>
            <Typography color="text.secondary">Framework: {displayFramework}</Typography>
          </Stack>

          <Stack spacing={1}>
            <Typography variant="subtitle2">Pricing snapshot</Typography>
            <Stack direction="row" justifyContent="space-between">
              <Typography color="text.secondary">Base fee</Typography>
              <Typography>{formatCurrency(scopeTotals.baseTotal)}</Typography>
            </Stack>
            <Stack direction="row" justifyContent="space-between">
              <Typography color="text.secondary">Optional delta</Typography>
              <Typography>{formatCurrency(scopeTotals.optionalTotal)}</Typography>
            </Stack>
            <Stack direction="row" justifyContent="space-between">
              <Typography color="text.secondary">Total with options</Typography>
              <Typography>{formatCurrency(scopeTotals.total)}</Typography>
            </Stack>
          </Stack>

          <Stack spacing={1}>
            <Typography variant="subtitle2">Delivery impact</Typography>
            <Stack direction="row" justifyContent="space-between">
              <Typography color="text.secondary">Services</Typography>
              <Typography>{servicesCount}</Typography>
            </Stack>
            <Stack direction="row" justifyContent="space-between">
              <Typography color="text.secondary">Planned cycles</Typography>
              <Typography>{plannedReviewCycles}</Typography>
            </Stack>
          </Stack>

          <Stack spacing={1}>
            <Typography variant="subtitle2">Billing</Typography>
            <Stack direction="row" justifyContent="space-between">
              <Typography color="text.secondary">Periods</Typography>
              <Typography>{billingPeriods}</Typography>
            </Stack>
            <Stack direction="row" justifyContent="space-between">
              <Typography color="text.secondary">Avg monthly</Typography>
              <Typography>{formatCurrency(billingAverage)}</Typography>
            </Stack>
          </Stack>

          <Stack spacing={1}>
            <Typography variant="subtitle2">Assumptions & exclusions</Typography>
            <Stack direction="row" justifyContent="space-between">
              <Typography color="text.secondary">Assumptions</Typography>
              <Typography>{assumptionCount}</Typography>
            </Stack>
            <Stack direction="row" justifyContent="space-between">
              <Typography color="text.secondary">Exclusions</Typography>
              <Typography>{exclusionCount}</Typography>
            </Stack>
          </Stack>

          <Stack spacing={1}>
            <Typography variant="subtitle2">Award readiness</Typography>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Chip
                color={readinessScore >= 100 ? 'success' : readinessScore >= 60 ? 'warning' : 'default'}
                label={`${readinessScore}% Ready`}
                size="small"
              />
              <Button size="small" onClick={() => setReadinessDialogOpen(true)}>
                View checklist
              </Button>
            </Stack>
          </Stack>
        </Stack>
      </Paper>

      <Box>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
          Bid workspace
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          {displayName} - {displayStatus}
        </Typography>

        <Tabs value={tab} onChange={(_, value) => setTab(value)} sx={{ mb: 2 }}>
          <Tab label="Overview" />
          <Tab label="Services" />
          <Tab label="Stages & Cycles" />
          <Tab label="Pricing" />
          <Tab label="Cashflow" />
          <Tab label="Assumptions/Exclusions" />
          <Tab label="Convert/Award" />
        </Tabs>
        {tab === 0 && (
        <Stack spacing={2} sx={{ maxWidth: 900 }}>
          {overviewMessage && <Alert severity="info">{overviewMessage}</Alert>}
          <TextField
            label="Bid name"
            value={overviewState.bid_name ?? ''}
            onChange={(event) => setOverviewState((prev) => ({ ...prev, bid_name: event.target.value }))}
          />
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <FormControl fullWidth>
              <InputLabel>Type</InputLabel>
              <Select
                label="Type"
                value={overviewState.bid_type ?? 'PROPOSAL'}
                onChange={(event) => setOverviewState((prev) => ({ ...prev, bid_type: event.target.value }))}
              >
                {BID_TYPES.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                label="Status"
                value={overviewState.status ?? 'DRAFT'}
                onChange={(event) => setOverviewState((prev) => ({ ...prev, status: event.target.value }))}
              >
                {BID_STATUSES.map((status) => (
                  <MenuItem key={status} value={status}>
                    {status}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <FormControl fullWidth>
              <InputLabel>Client</InputLabel>
              <Select
                label="Client"
                value={overviewState.client_id ?? ''}
                onChange={(event) =>
                  setOverviewState((prev) => ({
                    ...prev,
                    client_id: event.target.value === '' ? undefined : Number(event.target.value),
                  }))
                }
              >
                <MenuItem value="">Unassigned</MenuItem>
                {(clients ?? []).map((client) => (
                  <MenuItem key={client.client_id} value={client.client_id}>
                    {client.client_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Project</InputLabel>
              <Select
                label="Project"
                value={overviewState.project_id ?? ''}
                onChange={(event) =>
                  setOverviewState((prev) => ({
                    ...prev,
                    project_id: event.target.value === '' ? undefined : Number(event.target.value),
                  }))
                }
              >
                <MenuItem value="">Opportunity</MenuItem>
                {(projects ?? []).map((project) => (
                  <MenuItem key={project.project_id} value={project.project_id}>
                    {project.project_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              label="Probability %"
              type="number"
              value={overviewState.probability ?? ''}
              onChange={(event) =>
                setOverviewState((prev) => ({
                  ...prev,
                  probability: event.target.value === '' ? undefined : Number(event.target.value),
                }))
              }
            />
            <FormControl fullWidth>
              <InputLabel>Owner</InputLabel>
              <Select
                label="Owner"
                value={overviewState.owner_user_id ?? ''}
                onChange={(event) =>
                  setOverviewState((prev) => ({
                    ...prev,
                    owner_user_id: event.target.value === '' ? undefined : Number(event.target.value),
                  }))
                }
              >
                <MenuItem value="">Unassigned</MenuItem>
                {(users ?? []).map((user) => (
                  <MenuItem key={user.user_id} value={user.user_id}>
                    {user.name || user.full_name || user.username}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              label="Currency"
              value={overviewState.currency_code ?? 'AUD'}
              onChange={(event) => setOverviewState((prev) => ({ ...prev, currency_code: event.target.value }))}
            />
            <TextField
              label="Stage framework"
              value={overviewState.stage_framework ?? 'CUSTOM'}
              onChange={(event) => setOverviewState((prev) => ({ ...prev, stage_framework: event.target.value }))}
            />
          </Stack>
          <TextField
            label="Validity days"
            type="number"
            value={overviewState.validity_days ?? ''}
            onChange={(event) =>
              setOverviewState((prev) => ({
                ...prev,
                validity_days: event.target.value === '' ? undefined : Number(event.target.value),
              }))
            }
          />
          <TextField
            label="PI notes"
            multiline
            minRows={2}
            value={overviewState.pi_notes ?? ''}
            onChange={(event) => setOverviewState((prev) => ({ ...prev, pi_notes: event.target.value }))}
          />
          <Button variant="contained" onClick={handleSaveOverview}>
            Save overview
          </Button>
        </Stack>
      )}

        {tab === 1 && (
        <Box>
          <Stack direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
            <Typography variant="h6">Services</Typography>
            <Button variant="outlined" onClick={() => clearScopeSelection()}>
              New service
            </Button>
          </Stack>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' },
              gap: 2,
              alignItems: 'start',
            }}
          >
            <Box>
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                spacing={2}
                alignItems={{ xs: 'stretch', sm: 'center' }}
                sx={{ mb: 2 }}
              >
                <FormControl size="small" sx={{ minWidth: 240 }}>
                  <InputLabel id="bid-scope-template-label">Scope template</InputLabel>
                  <Select
                    labelId="bid-scope-template-label"
                    label="Scope template"
                    value={selectedScopeTemplate}
                    onChange={(event) => setSelectedScopeTemplate(event.target.value)}
                    disabled={!schemaReady}
                  >
                    {(scopeTemplates ?? []).map((template) => (
                      <MenuItem key={template.name} value={template.name}>
                        {template.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={replaceScopeItems}
                      onChange={(event) => setReplaceScopeItems(event.target.checked)}
                    />
                  }
                  label="Replace existing scope items"
                />
                <Button
                  variant="contained"
                  onClick={applyScopeTemplate}
                  disabled={!schemaReady || !selectedScopeTemplate}
                >
                  Apply template
                </Button>
              </Stack>
              {templateApplyError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {templateApplyError}
                </Alert>
              )}
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Title</TableCell>
                    <TableCell>Stage</TableCell>
                    <TableCell>Unit</TableCell>
                    <TableCell>Qty</TableCell>
                    <TableCell>Rate</TableCell>
                    <TableCell>Lump sum</TableCell>
                    <TableCell>Optional</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(scopeItems ?? []).map((item) => (
                    <TableRow
                      key={item.scope_item_id}
                      hover
                      selected={scopeForm.scope_item_id === item.scope_item_id}
                      onClick={() => selectScopeItem(item)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>{item.title}</TableCell>
                      <TableCell>{item.stage_name || '?'}</TableCell>
                      <TableCell>{item.unit || '?'}</TableCell>
                      <TableCell>{item.included_qty ?? '?'}</TableCell>
                      <TableCell>{item.unit_rate ?? '?'}</TableCell>
                      <TableCell>{item.lump_sum ?? '?'}</TableCell>
                      <TableCell>{item.is_optional ? 'Yes' : 'No'}</TableCell>
                    </TableRow>
                  ))}
                  {(scopeItems ?? []).length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7}>
                        <Alert severity="info">No services yet.</Alert>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </Box>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Stack spacing={2}>
                <Typography variant="subtitle1">
                  {scopeForm.scope_item_id ? 'Edit service' : 'New service'}
                </Typography>
                {scopeError && <Alert severity="error">{scopeError}</Alert>}
                <TextField
                  label="Title"
                  value={scopeForm.title ?? ''}
                  onChange={(event) => setScopeForm((prev) => ({ ...prev, title: event.target.value }))}
                />
                <TextField
                  label="Stage"
                  value={scopeForm.stage_name ?? ''}
                  onChange={(event) => setScopeForm((prev) => ({ ...prev, stage_name: event.target.value }))}
                />
                <TextField
                  label="Description"
                  multiline
                  minRows={2}
                  value={scopeForm.description ?? ''}
                  onChange={(event) => setScopeForm((prev) => ({ ...prev, description: event.target.value }))}
                />
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                  <TextField
                    label="Unit"
                    value={scopeForm.unit ?? ''}
                    onChange={(event) => setScopeForm((prev) => ({ ...prev, unit: event.target.value }))}
                  />
                  <TextField
                    label="Included qty"
                    type="number"
                    value={scopeForm.included_qty ?? ''}
                    onChange={(event) =>
                      setScopeForm((prev) => ({
                        ...prev,
                        included_qty: event.target.value === '' ? undefined : Number(event.target.value),
                      }))
                    }
                  />
                </Stack>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                  <TextField
                    label="Unit rate"
                    type="number"
                    value={scopeForm.unit_rate ?? ''}
                    onChange={(event) =>
                      setScopeForm((prev) => ({
                        ...prev,
                        unit_rate: event.target.value === '' ? undefined : Number(event.target.value),
                      }))
                    }
                  />
                  <TextField
                    label="Lump sum"
                    type="number"
                    value={scopeForm.lump_sum ?? ''}
                    onChange={(event) =>
                      setScopeForm((prev) => ({
                        ...prev,
                        lump_sum: event.target.value === '' ? undefined : Number(event.target.value),
                      }))
                    }
                  />
                </Stack>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={Boolean(scopeForm.is_optional)}
                      onChange={(event) =>
                        setScopeForm((prev) => ({ ...prev, is_optional: event.target.checked }))
                      }
                    />
                  }
                  label="Optional service"
                />
                <Stack direction="row" spacing={2}>
                  <Button variant="contained" onClick={saveScopeItem}>
                    Save service
                  </Button>
                  <Button
                    color="error"
                    disabled={!scopeForm.scope_item_id}
                    onClick={async () => {
                      if (!scopeForm.scope_item_id) {
                        return;
                      }
                      await bidsApi.deleteScopeItem(bidId, scopeForm.scope_item_id);
                      clearScopeSelection();
                      queryClient.invalidateQueries({ queryKey: ['bid', bidId, 'scope-items'] });
                    }}
                  >
                    Delete
                  </Button>
                </Stack>
              </Stack>
            </Paper>
          </Box>
        </Box>
      )}

        {tab === 2 && (
        <Box>
          <Stack direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
            <Typography variant="h6">Program stages</Typography>
            <Button variant="outlined" onClick={() => openProgramDialog()}>
              Add stage
            </Button>
          </Stack>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Stage</TableCell>
                <TableCell>Start</TableCell>
                <TableCell>End</TableCell>
                <TableCell>Cadence</TableCell>
                <TableCell>Cycles</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(programStages ?? []).map((stage) => (
                <TableRow key={stage.program_stage_id}>
                  <TableCell>{stage.stage_name}</TableCell>
                  <TableCell>{stage.planned_start || '?'}</TableCell>
                  <TableCell>{stage.planned_end || '?'}</TableCell>
                  <TableCell>{stage.cadence || '?'}</TableCell>
                  <TableCell>{stage.cycles_planned ?? '?'}</TableCell>
                  <TableCell>
                    <Button size="small" onClick={() => openProgramDialog(stage)}>
                      Edit
                    </Button>
                    <Button
                      size="small"
                      color="error"
                      onClick={async () => {
                        await bidsApi.deleteProgramStage(bidId, stage.program_stage_id);
                        queryClient.invalidateQueries({ queryKey: ['bid', bidId, 'program-stages'] });
                      }}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {(programStages ?? []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={6}>
                    <Alert severity="info">No program stages yet.</Alert>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Box>
      )}

        {tab === 3 && (
        <Stack spacing={2}>
          <Alert severity="info">
            Pricing totals are derived from scope items. Update scope items to refresh the totals.
          </Alert>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
              <Typography variant="subtitle2">Lump sum total</Typography>
              <Typography variant="h6">{formatCurrency(scopeTotals.totalLumpSum)}</Typography>
            </Box>
            <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
              <Typography variant="subtitle2">Unit-based total</Typography>
              <Typography variant="h6">{formatCurrency(scopeTotals.totalUnitValue)}</Typography>
            </Box>
            <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
              <Typography variant="subtitle2">Scope total</Typography>
              <Typography variant="h6">{formatCurrency(scopeTotals.total)}</Typography>
            </Box>
          </Stack>
          <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
            <Typography variant="subtitle2">Billing schedule total</Typography>
            <Typography variant="h6">{formatCurrency(billingTotal)}</Typography>
          </Box>
        </Stack>
      )}

        {tab === 4 && (
        <Box>
          <Stack direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
            <Typography variant="h6">Billing schedule</Typography>
            <Button variant="outlined" onClick={() => openBillingDialog()}>
              Add line
            </Button>
          </Stack>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Period start</TableCell>
                <TableCell>Period end</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Notes</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(billingSchedule ?? []).map((line) => (
                <TableRow key={line.billing_line_id}>
                  <TableCell>{line.period_start}</TableCell>
                  <TableCell>{line.period_end}</TableCell>
                  <TableCell>{formatCurrency(Number(line.amount || 0))}</TableCell>
                  <TableCell>{line.notes || '?'}</TableCell>
                  <TableCell>
                    <Button size="small" onClick={() => openBillingDialog(line)}>
                      Edit
                    </Button>
                    <Button
                      size="small"
                      color="error"
                      onClick={async () => {
                        await bidsApi.deleteBillingLine(bidId, line.billing_line_id);
                        queryClient.invalidateQueries({ queryKey: ['bid', bidId, 'billing-schedule'] });
                      }}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {(billingSchedule ?? []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={5}>
                    <Alert severity="info">No billing schedule yet.</Alert>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Box>
      )}
        {tab === 5 && (
        <Stack spacing={2} sx={{ maxWidth: 900 }}>
          {sectionsMessage && <Alert severity="info">{sectionsMessage}</Alert>}
          <Accordion
            expanded={sectionsExpanded.assumptions}
            onChange={(_, expanded) =>
              setSectionsExpanded((prev) => ({ ...prev, assumptions: expanded }))
            }
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography>Assumptions</Typography>
                <Chip size="small" label={assumptionCount} />
              </Stack>
            </AccordionSummary>
            <AccordionDetails>
              <TextField
                label="Assumptions (one per line)"
                multiline
                minRows={4}
                fullWidth
                value={assumptionsText}
                onChange={(event) => setAssumptionsText(event.target.value)}
              />
            </AccordionDetails>
          </Accordion>
          <Accordion
            expanded={sectionsExpanded.exclusions}
            onChange={(_, expanded) =>
              setSectionsExpanded((prev) => ({ ...prev, exclusions: expanded }))
            }
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography>Exclusions</Typography>
                <Chip size="small" label={exclusionCount} />
              </Stack>
            </AccordionSummary>
            <AccordionDetails>
              <TextField
                label="Exclusions (one per line)"
                multiline
                minRows={4}
                fullWidth
                value={exclusionsText}
                onChange={(event) => setExclusionsText(event.target.value)}
              />
            </AccordionDetails>
          </Accordion>
          <Accordion
            expanded={sectionsExpanded.methodology}
            onChange={(_, expanded) =>
              setSectionsExpanded((prev) => ({ ...prev, methodology: expanded }))
            }
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography>Methodology</Typography>
                <Chip size="small" label={methodologyCount} />
              </Stack>
            </AccordionSummary>
            <AccordionDetails>
              <TextField
                label="Methodology (one per line)"
                multiline
                minRows={4}
                fullWidth
                value={methodologyText}
                onChange={(event) => setMethodologyText(event.target.value)}
              />
            </AccordionDetails>
          </Accordion>
          <Accordion
            expanded={sectionsExpanded.options}
            onChange={(_, expanded) =>
              setSectionsExpanded((prev) => ({ ...prev, options: expanded }))
            }
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography>Options</Typography>
                <Chip size="small" label={optionsCount} />
              </Stack>
            </AccordionSummary>
            <AccordionDetails>
              <TextField
                label="Options (one per line)"
                multiline
                minRows={4}
                fullWidth
                value={optionsText}
                onChange={(event) => setOptionsText(event.target.value)}
              />
            </AccordionDetails>
          </Accordion>
          <Button variant="contained" onClick={handleSaveSections}>
            Save sections
          </Button>
        </Stack>
      )}

        {tab === 6 && (
        <Stack spacing={2} sx={{ maxWidth: 900 }}>
          {awardMessage && <Alert severity="success">{awardMessage}</Alert>}
          {awardError && <Alert severity="error">{awardError}</Alert>}
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Stack spacing={1}>
              <Typography variant="subtitle2">Downstream impact preview</Typography>
              <Typography color="text.secondary">
                This bid will create {servicesCount} services and {plannedReviewCycles} review cycles.
              </Typography>
              <Typography color="text.secondary">
                Billing forecast: {billingPeriods} claim periods totaling {formatCurrency(billingTotal)}.
              </Typography>
            </Stack>
          </Paper>
          {readinessScore < 100 && (
            <Alert severity="warning">
              Award readiness is {readinessScore}%. Missing: {readinessMissing.join(', ') || 'n/a'}.
            </Alert>
          )}
          <FormControl>
            <InputLabel>Create new project</InputLabel>
            <Select
              label="Create new project"
              value={createNewProject ? 'yes' : 'no'}
              onChange={(event) => setCreateNewProject(event.target.value === 'yes')}
            >
              <MenuItem value="yes">Yes</MenuItem>
              <MenuItem value="no">No (use existing)</MenuItem>
            </Select>
          </FormControl>
          {createNewProject ? (
            <Stack spacing={2}>
              <TextField
                label="Project name"
                value={newProjectPayload.project_name}
                onChange={(event) =>
                  setNewProjectPayload((prev) => ({ ...prev, project_name: event.target.value }))
                }
              />
              <TextField
                label="Status"
                value={newProjectPayload.status}
                onChange={(event) =>
                  setNewProjectPayload((prev) => ({ ...prev, status: event.target.value }))
                }
              />
            </Stack>
          ) : (
            <FormControl>
              <InputLabel>Project</InputLabel>
              <Select
                label="Project"
                value={awardProjectId}
                onChange={(event) =>
                  setAwardProjectId(event.target.value === '' ? '' : Number(event.target.value))
                }
              >
                <MenuItem value="">Select project</MenuItem>
                {(projects ?? []).map((project) => (
                  <MenuItem key={project.project_id} value={project.project_id}>
                    {project.project_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          <Button variant="contained" onClick={handleAward}>
            Convert to project
          </Button>
          {awardResult && (
            <Alert severity="info">
              Project {awardResult.project_id} created. Services: {awardResult.created_services}, Reviews:{' '}
              {awardResult.created_reviews}, Claims: {awardResult.created_claims}.
            </Alert>
          )}
        </Stack>
      )}
      </Box>

      <Dialog open={readinessDialogOpen} onClose={() => setReadinessDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Award readiness checklist</DialogTitle>
        <DialogContent>
          <Stack spacing={1} sx={{ mt: 1 }}>
            {readinessChecks.map((check) => (
              <Stack key={check.key} direction="row" justifyContent="space-between" alignItems="center">
                <Typography>{check.label}</Typography>
                <Chip
                  size="small"
                  color={check.ok ? 'success' : 'default'}
                  label={check.ok ? 'Complete' : 'Missing'}
                />
              </Stack>
            ))}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReadinessDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={programDialogOpen} onClose={() => setProgramDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{programForm.program_stage_id ? 'Edit stage' : 'Add stage'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {programError && <Alert severity="error">{programError}</Alert>}
            <TextField
              label="Stage name"
              value={programForm.stage_name ?? ''}
              onChange={(event) => setProgramForm((prev) => ({ ...prev, stage_name: event.target.value }))}
            />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Planned start"
                type="date"
                InputLabelProps={{ shrink: true }}
                value={programForm.planned_start ?? ''}
                onChange={(event) => setProgramForm((prev) => ({ ...prev, planned_start: event.target.value }))}
              />
              <TextField
                label="Planned end"
                type="date"
                InputLabelProps={{ shrink: true }}
                value={programForm.planned_end ?? ''}
                onChange={(event) => setProgramForm((prev) => ({ ...prev, planned_end: event.target.value }))}
              />
            </Stack>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <FormControl>
                <InputLabel id="bid-program-cadence-label">Cadence</InputLabel>
                <Select
                  labelId="bid-program-cadence-label"
                  label="Cadence"
                  value={programForm.cadence ?? ''}
                  onChange={(event) => setProgramForm((prev) => ({ ...prev, cadence: event.target.value }))}
                >
                  {PROGRAM_CADENCES.map((cadence) => (
                    <MenuItem key={cadence} value={cadence}>
                      {cadence.charAt(0).toUpperCase() + cadence.slice(1)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                label="Cycles planned"
                type="number"
                value={programForm.cycles_planned ?? ''}
                onChange={(event) =>
                  setProgramForm((prev) => ({
                    ...prev,
                    cycles_planned: event.target.value === '' ? undefined : Number(event.target.value),
                  }))
                }
              />
            </Stack>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setProgramDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={saveProgramStage}>
            Save
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={billingDialogOpen} onClose={() => setBillingDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{billingForm.billing_line_id ? 'Edit billing line' : 'Add billing line'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {billingError && <Alert severity="error">{billingError}</Alert>}
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="Period start"
                type="date"
                InputLabelProps={{ shrink: true }}
                value={billingForm.period_start ?? ''}
                onChange={(event) => setBillingForm((prev) => ({ ...prev, period_start: event.target.value }))}
              />
              <TextField
                label="Period end"
                type="date"
                InputLabelProps={{ shrink: true }}
                value={billingForm.period_end ?? ''}
                onChange={(event) => setBillingForm((prev) => ({ ...prev, period_end: event.target.value }))}
              />
            </Stack>
            <TextField
              label="Amount"
              type="number"
              value={billingForm.amount ?? ''}
              onChange={(event) =>
                setBillingForm((prev) => ({
                  ...prev,
                  amount: event.target.value === '' ? undefined : Number(event.target.value),
                }))
              }
            />
            <TextField
              label="Notes"
              value={billingForm.notes ?? ''}
              onChange={(event) => setBillingForm((prev) => ({ ...prev, notes: event.target.value }))}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBillingDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={saveBillingLine}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
