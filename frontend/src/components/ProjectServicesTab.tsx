import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
  LinearProgress,
  Checkbox,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { projectServicesApi, serviceReviewsApi, serviceItemsApi } from '@/api';
import type { ProjectService, ServiceReview, ServiceItem } from '@/types/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 1 }}>{children}</Box>}
    </div>
  );
}

interface ProjectServicesTabProps {
  projectId: number;
}

const BILL_RULES = [
  'Fixed Fee',
  'Time & Materials',
  'Percentage of Construction Cost',
  'Milestone Based',
  'Other'
];

const REVIEW_STATUSES = [
  'planned',
  'in_progress',
  'completed',
  'overdue',
  'cancelled'
];

const ITEM_TYPES = [
  'review',
  'audit',
  'deliverable',
  'milestone',
  'inspection',
  'meeting',
  'other'
];

const ITEM_STATUSES = [
  'planned',
  'in_progress',
  'completed',
  'overdue',
  'cancelled'
];

const ITEM_PRIORITIES = [
  'low',
  'medium',
  'high',
  'critical'
];

export function ProjectServicesTab({ projectId }: ProjectServicesTabProps) {
  const queryClient = useQueryClient();
  const [serviceTabValue, setServiceTabValue] = useState(0);
  const [selectedService, setSelectedService] = useState<ProjectService | null>(null);
  const [selectedReview, setSelectedReview] = useState<ServiceReview | null>(null);
  const [selectedItem, setSelectedItem] = useState<ServiceItem | null>(null);
  const [serviceDialogOpen, setServiceDialogOpen] = useState(false);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [itemDialogOpen, setItemDialogOpen] = useState(false);
  const [serviceFormData, setServiceFormData] = useState({
    service_code: '',
    service_name: '',
    phase: '',
    unit_type: '',
    unit_qty: 0,
    unit_rate: 0,
    lump_sum_fee: 0,
    agreed_fee: 0,
    bill_rule: '',
    notes: '',
  });
  const [reviewFormData, setReviewFormData] = useState({
    cycle_no: 1,
    planned_date: '',
    due_date: '',
    disciplines: '',
    deliverables: '',
    status: 'planned',
    weight_factor: 1.0,
    evidence_links: '',
    is_billed: false,
  });
  const [itemFormData, setItemFormData] = useState({
    item_type: 'review',
    title: '',
    description: '',
    planned_date: '',
    due_date: '',
    actual_date: '',
    status: 'planned',
    priority: 'medium',
    assigned_to: '',
    evidence_links: '',
    notes: '',
    is_billed: false,
  });

  // Fetch project services
  const {
    data: services,
    isLoading: servicesLoading,
    error: servicesError,
  } = useQuery({
    queryKey: ['projectServices', projectId],
    queryFn: () => projectServicesApi.getAll(projectId),
  });

  // Fetch service reviews when a service is selected
  const {
    data: reviews,
  } = useQuery({
    queryKey: ['serviceReviews', projectId, selectedService?.service_id],
    queryFn: async () => {
      if (!selectedService) return [];
      const response = await serviceReviewsApi.getAll(projectId, selectedService.service_id);
      return response.data;
    },
    enabled: !!selectedService,
  });

  // Fetch service items when a service is selected
  const {
    data: serviceItems,
  } = useQuery({
    queryKey: ['serviceItems', projectId, selectedService?.service_id],
    queryFn: async () => {
      if (!selectedService) return [];
      const response = await serviceItemsApi.getAll(projectId, selectedService.service_id);
      return response.data;
    },
    enabled: !!selectedService,
  });

  const servicesData: ProjectService[] = services?.data ?? [];

  const currencyFormatter = useMemo(
    () => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }),
    []
  );

  const formatCurrency = (value?: number | null) =>
    currencyFormatter.format(value === undefined || value === null ? 0 : value);

  const formatPercent = (value?: number | null) => {
    const numeric = value === undefined || value === null ? 0 : value;
    return `${numeric.toFixed(1)}%`;
  };

  const billingSummary = useMemo(() => {
    const totals = servicesData.reduce(
      (acc, service) => {
        const agreed = service.agreed_fee ?? 0;
        const billed =
          service.billed_amount ?? service.claimed_to_date ?? 0;
        acc.totalAgreed += agreed;
        acc.totalBilled += billed;
        return acc;
      },
      { totalAgreed: 0, totalBilled: 0 }
    );
    const totalRemaining = Math.max(totals.totalAgreed - totals.totalBilled, 0);
    const progress =
      totals.totalAgreed > 0 ? (totals.totalBilled / totals.totalAgreed) * 100 : 0;
    return {
      totalAgreed: totals.totalAgreed,
      totalBilled: totals.totalBilled,
      totalRemaining,
      progress: Math.min(Math.max(progress, 0), 100),
    };
  }, [servicesData]);

  const getStatusColor = (
    status: string
  ): 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning' => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'primary';
      case 'overdue':
        return 'error';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Service mutations
  const createServiceMutation = useMutation({
    mutationFn: (data: typeof serviceFormData) => projectServicesApi.create(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projectServices', projectId] });
      handleCloseServiceDialog();
    },
  });

  const updateServiceMutation = useMutation({
    mutationFn: ({ serviceId, data }: { serviceId: number; data: Partial<typeof serviceFormData> }) =>
      projectServicesApi.update(projectId, serviceId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projectServices', projectId] });
      handleCloseServiceDialog();
    },
  });

  const deleteServiceMutation = useMutation({
    mutationFn: (serviceId: number) => projectServicesApi.delete(projectId, serviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projectServices', projectId] });
    },
  });

  // Review mutations
  const createReviewMutation = useMutation({
    mutationFn: (data: typeof reviewFormData) =>
      selectedService ? serviceReviewsApi.create(projectId, selectedService.service_id, data) : Promise.reject('No service selected'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, selectedService?.service_id] });
      handleCloseReviewDialog();
    },
  });

  const updateReviewMutation = useMutation({
    mutationFn: ({ reviewId, data }: { reviewId: number; data: Partial<typeof reviewFormData> }) =>
      selectedService ? serviceReviewsApi.update(projectId, selectedService.service_id, reviewId, data) : Promise.reject('No service selected'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, selectedService?.service_id] });
      handleCloseReviewDialog();
    },
  });

  const deleteReviewMutation = useMutation({
    mutationFn: (reviewId: number) => 
      selectedService ? serviceReviewsApi.delete(projectId, selectedService.service_id, reviewId) : Promise.reject('No service selected'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, selectedService?.service_id] });
    },
  });

  // Item mutations
  const createItemMutation = useMutation({
    mutationFn: (data: typeof itemFormData) =>
      selectedService ? serviceItemsApi.create(projectId, selectedService.service_id, data) : Promise.reject('No service selected'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceItems', projectId, selectedService?.service_id] });
      handleCloseItemDialog();
    },
  });

  const updateItemMutation = useMutation({
    mutationFn: ({ itemId, data }: { itemId: number; data: Partial<ServiceItem> }) =>
      selectedService ? serviceItemsApi.update(projectId, selectedService.service_id, itemId, data) : Promise.reject('No service selected'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceItems', projectId, selectedService?.service_id] });
      handleCloseItemDialog();
    },
  });

  const deleteItemMutation = useMutation({
    mutationFn: (itemId: number) => 
      selectedService ? serviceItemsApi.delete(projectId, selectedService.service_id, itemId) : Promise.reject('No service selected'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['serviceItems', projectId, selectedService?.service_id] });
    },
  });

  const handleOpenServiceDialog = (service?: ProjectService) => {
    if (service) {
      setSelectedService(service);
      setServiceFormData({
        service_code: service.service_code,
        service_name: service.service_name,
        phase: service.phase || '',
        unit_type: service.unit_type || '',
        unit_qty: service.unit_qty || 0,
        unit_rate: service.unit_rate || 0,
        lump_sum_fee: service.lump_sum_fee || 0,
        agreed_fee: service.agreed_fee || 0,
        bill_rule: service.bill_rule || '',
        notes: service.notes || '',
      });
    } else {
      setSelectedService(null);
      setServiceFormData({
        service_code: '',
        service_name: '',
        phase: '',
        unit_type: '',
        unit_qty: 0,
        unit_rate: 0,
        lump_sum_fee: 0,
        agreed_fee: 0,
        bill_rule: '',
        notes: '',
      });
    }
    setServiceDialogOpen(true);
  };

  const handleCloseServiceDialog = () => {
    setServiceDialogOpen(false);
    setSelectedService(null);
  };

  const handleOpenReviewDialog = (review?: ServiceReview) => {
    if (review) {
      setSelectedReview(review);
      setReviewFormData({
        cycle_no: review.cycle_no,
        planned_date: review.planned_date,
        due_date: review.due_date || '',
        disciplines: review.disciplines || '',
        deliverables: review.deliverables || '',
        status: review.status,
        weight_factor: review.weight_factor,
        evidence_links: review.evidence_links || '',
        is_billed: review.is_billed ?? (review.status === 'completed'),
      });
    } else {
      setSelectedReview(null);
      setReviewFormData({
        cycle_no: (reviews?.length || 0) + 1,
        planned_date: '',
        due_date: '',
        disciplines: '',
        deliverables: '',
        status: 'planned',
        weight_factor: 1.0,
        evidence_links: '',
        is_billed: false,
      });
    }
    setReviewDialogOpen(true);
  };

  const handleCloseReviewDialog = () => {
    setReviewDialogOpen(false);
    setSelectedReview(null);
  };

  const handleOpenItemDialog = (item?: ServiceItem) => {
    if (item) {
      setSelectedItem(item);
      setItemFormData({
        item_type: item.item_type,
        title: item.title,
        description: item.description || '',
        planned_date: item.planned_date || '',
        due_date: item.due_date || '',
        actual_date: item.actual_date || '',
        status: item.status,
        priority: item.priority,
        assigned_to: item.assigned_to || '',
        evidence_links: item.evidence_links || '',
        notes: item.notes || '',
        is_billed: item.is_billed ?? (item.status === 'completed'),
      });
    } else {
      setSelectedItem(null);
      setItemFormData({
        item_type: 'review',
        title: '',
        description: '',
        planned_date: '',
        due_date: '',
        actual_date: '',
        status: 'planned',
        priority: 'medium',
        assigned_to: '',
        evidence_links: '',
        notes: '',
        is_billed: false,
      });
    }
    setItemDialogOpen(true);
  };

  const handleCloseItemDialog = () => {
    setItemDialogOpen(false);
    setSelectedItem(null);
  };

  const handleServiceSubmit = () => {
    if (selectedService) {
      updateServiceMutation.mutate({ serviceId: selectedService.service_id, data: serviceFormData });
    } else {
      createServiceMutation.mutate(serviceFormData);
    }
  };

  const handleReviewSubmit = () => {
    if (!selectedService) return;

    if (selectedReview) {
      updateReviewMutation.mutate({ reviewId: selectedReview.review_id, data: reviewFormData });
    } else {
      createReviewMutation.mutate(reviewFormData);
    }
  };

  const handleItemSubmit = () => {
    if (!selectedService) return;

    if (selectedItem) {
      updateItemMutation.mutate({ itemId: selectedItem.item_id, data: itemFormData as Partial<ServiceItem> });
    } else {
      createItemMutation.mutate(itemFormData);
    }
  };

  const handleDeleteService = (serviceId: number) => {
    if (window.confirm('Are you sure you want to delete this service?')) {
      deleteServiceMutation.mutate(serviceId);
    }
  };

  const handleDeleteReview = (reviewId: number) => {
    if (window.confirm('Are you sure you want to delete this review?')) {
      deleteReviewMutation.mutate(reviewId);
    }
  };

  const handleDeleteItem = (itemId: number) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      deleteItemMutation.mutate(itemId);
    }
  };

  const handleServiceSelect = (service: ProjectService) => {
    setSelectedService(service);
    setServiceTabValue(1); // Switch to reviews tab
  };

  if (servicesLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (servicesError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load services: {servicesError.message}
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Project Services</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenServiceDialog()}
        >
          Add Service
        </Button>
      </Box>

      <Box display="flex" flexWrap="wrap" gap={2} mb={3}>
        <Paper sx={{ p: 2, flex: '1 1 220px', minWidth: 200 }} elevation={1}>
          <Typography variant="subtitle2" color="text.secondary">
            Total Contract Sum
          </Typography>
          <Typography variant="h6">
            {formatCurrency(billingSummary.totalAgreed)}
          </Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: '1 1 220px', minWidth: 200 }} elevation={1}>
          <Typography variant="subtitle2" color="text.secondary">
            Fee Billed
          </Typography>
          <Typography variant="h6">
            {formatCurrency(billingSummary.totalBilled)}
          </Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: '1 1 240px', minWidth: 220 }} elevation={1}>
          <Typography variant="subtitle2" color="text.secondary">
            Agreed Fee Remaining
          </Typography>
          <Typography variant="h6">
            {formatCurrency(billingSummary.totalRemaining)}
          </Typography>
          <Box mt={1}>
            <LinearProgress
              variant="determinate"
              value={billingSummary.progress}
              sx={{ height: 8, borderRadius: 4 }}
            />
            <Typography variant="caption" color="text.secondary">
              {formatPercent(billingSummary.progress)} billed
            </Typography>
          </Box>
        </Paper>
      </Box>

      <Tabs value={serviceTabValue} onChange={(_, newValue) => {
        // Prevent switching to reviews/items tabs if no service is selected
        if ((newValue === 1 || newValue === 2) && !selectedService) return;
        setServiceTabValue(newValue);
      }}>
        <Tab label="Services" />
        <Tab label="Reviews" disabled={!selectedService} />
        <Tab label="Items" disabled={!selectedService} />
      </Tabs>

      <TabPanel value={serviceTabValue} index={0}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Code</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Phase</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Agreed Fee</TableCell>
                <TableCell>Billed</TableCell>
                <TableCell>Remaining</TableCell>
                <TableCell>Progress</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {servicesData.map((service) => (
                <TableRow key={service.service_id}>
                  <TableCell>{service.service_code}</TableCell>
                  <TableCell>{service.service_name}</TableCell>
                  <TableCell>{service.phase || '-'}</TableCell>
                  <TableCell>
                    <Chip
                      label={service.status}
                      color={getStatusColor(service.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{formatCurrency(service.agreed_fee)}</TableCell>
                  <TableCell>{formatCurrency(service.billed_amount ?? service.claimed_to_date)}</TableCell>
                  <TableCell>{formatCurrency(service.agreed_fee_remaining)}</TableCell>
                  <TableCell sx={{ minWidth: 180 }}>
                    <Box>
                      <LinearProgress
                        variant="determinate"
                        value={service.billing_progress_pct ?? service.progress_pct ?? 0}
                        sx={{ height: 8, borderRadius: 4, mb: 0.5 }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {formatPercent(service.billing_progress_pct ?? service.progress_pct)} billed
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <IconButton size="small" onClick={() => handleServiceSelect(service)}>
                      <AssessmentIcon />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleOpenServiceDialog(service)}>
                      <EditIcon />
                    </IconButton>
                    <IconButton size="small" color="error" onClick={() => handleDeleteService(service.service_id)}>
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={serviceTabValue} index={1}>
        {selectedService && (
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Reviews for {selectedService.service_name}</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenReviewDialog()}
              >
                Add Review
              </Button>
            </Box>

            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Cycle</TableCell>
                    <TableCell>Planned Date</TableCell>
                    <TableCell>Due Date</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Weight</TableCell>
                    <TableCell>Billed</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {reviews?.map((review: ServiceReview) => (
                    <TableRow key={review.review_id}>
                      <TableCell>{review.cycle_no}</TableCell>
                      <TableCell>{new Date(review.planned_date).toLocaleDateString()}</TableCell>
                      <TableCell>{review.due_date ? new Date(review.due_date).toLocaleDateString() : '-'}</TableCell>
                      <TableCell>
                        <Chip
                          label={review.status}
                          color={review.status === 'completed' ? 'success' : review.status === 'in_progress' ? 'primary' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{review.weight_factor}</TableCell>
                      <TableCell>
                        <Chip
                          label={review.is_billed ? 'Yes' : 'No'}
                          color={review.is_billed ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <IconButton size="small" onClick={() => handleOpenReviewDialog(review)}>
                          <EditIcon />
                        </IconButton>
                        <IconButton size="small" color="error" onClick={() => handleDeleteReview(review.review_id)}>
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </TabPanel>

      <TabPanel value={serviceTabValue} index={2}>
        {selectedService && (
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Items for {selectedService.service_name}</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenItemDialog()}
              >
                Add Item
              </Button>
            </Box>

            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Planned Date</TableCell>
                    <TableCell>Due Date</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Priority</TableCell>
                    <TableCell>Billed</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {serviceItems?.map((item: ServiceItem) => (
                    <TableRow key={item.item_id}>
                      <TableCell>
                        <Chip
                          label={item.item_type}
                          color="info"
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{item.title}</TableCell>
                      <TableCell>{item.planned_date ? new Date(item.planned_date).toLocaleDateString() : '-'}</TableCell>
                      <TableCell>{item.due_date ? new Date(item.due_date).toLocaleDateString() : '-'}</TableCell>
                      <TableCell>
                        <Chip
                          label={item.status}
                          color={item.status === 'completed' ? 'success' : item.status === 'in_progress' ? 'primary' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={item.priority}
                          color={item.priority === 'critical' ? 'error' : item.priority === 'high' ? 'warning' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={item.is_billed ? 'Yes' : 'No'}
                          color={item.is_billed ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <IconButton size="small" onClick={() => handleOpenItemDialog(item)}>
                          <EditIcon />
                        </IconButton>
                        <IconButton size="small" color="error" onClick={() => handleDeleteItem(item.item_id)}>
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </TabPanel>

      {/* Service Dialog */}
      <Dialog open={serviceDialogOpen} onClose={handleCloseServiceDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedService ? 'Edit Service' : 'Create Service'}
        </DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Service Code"
              value={serviceFormData.service_code}
              onChange={(e) => setServiceFormData(prev => ({ ...prev, service_code: e.target.value }))}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Service Name"
              value={serviceFormData.service_name}
              onChange={(e) => setServiceFormData(prev => ({ ...prev, service_name: e.target.value }))}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Phase"
              value={serviceFormData.phase}
              onChange={(e) => setServiceFormData(prev => ({ ...prev, phase: e.target.value }))}
              margin="normal"
            />
            <TextField
              fullWidth
              select
              label="Bill Rule"
              value={serviceFormData.bill_rule}
              onChange={(e) => setServiceFormData(prev => ({ ...prev, bill_rule: e.target.value }))}
              margin="normal"
            >
              {BILL_RULES.map((rule) => (
                <MenuItem key={rule} value={rule}>
                  {rule}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              fullWidth
              type="number"
              label="Agreed Fee"
              value={serviceFormData.agreed_fee}
              onChange={(e) => setServiceFormData(prev => ({ ...prev, agreed_fee: parseFloat(e.target.value) || 0 }))}
              margin="normal"
            />
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Notes"
              value={serviceFormData.notes}
              onChange={(e) => setServiceFormData(prev => ({ ...prev, notes: e.target.value }))}
              margin="normal"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseServiceDialog}>Cancel</Button>
          <Button
            onClick={handleServiceSubmit}
            variant="contained"
            disabled={createServiceMutation.isPending || updateServiceMutation.isPending}
          >
            {createServiceMutation.isPending || updateServiceMutation.isPending ? (
              <CircularProgress size={20} />
            ) : (
              selectedService ? 'Update' : 'Create'
            )}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Review Dialog */}
      <Dialog open={reviewDialogOpen} onClose={handleCloseReviewDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedReview ? `Edit Review for ${selectedService?.service_name}` : `Add Review for ${selectedService?.service_name}`}
        </DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 2 }}>
            <TextField
              fullWidth
              type="number"
              label="Cycle Number"
              value={reviewFormData.cycle_no}
              onChange={(e) => setReviewFormData(prev => ({ ...prev, cycle_no: parseInt(e.target.value) || 1 }))}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              type="date"
              label="Planned Date"
              value={reviewFormData.planned_date}
              onChange={(e) => setReviewFormData(prev => ({ ...prev, planned_date: e.target.value }))}
              margin="normal"
              required
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              fullWidth
              type="date"
              label="Due Date"
              value={reviewFormData.due_date}
              onChange={(e) => setReviewFormData(prev => ({ ...prev, due_date: e.target.value }))}
              margin="normal"
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              fullWidth
              select
              label="Status"
              value={reviewFormData.status}
              onChange={(e) => {
                const nextStatus = e.target.value;
                setReviewFormData(prev => ({
                  ...prev,
                  status: nextStatus,
                  is_billed: nextStatus === 'completed'
                    ? true
                    : (prev.status === 'completed' ? false : prev.is_billed),
                }));
              }}
              margin="normal"
            >
              {REVIEW_STATUSES.map((status) => (
                <MenuItem key={status} value={status}>
                  {status}
                </MenuItem>
              ))}
            </TextField>
            <FormControlLabel
              control={
                <Checkbox
                  checked={reviewFormData.is_billed}
                  onChange={(e) =>
                    setReviewFormData(prev => ({
                      ...prev,
                      is_billed: e.target.checked,
                    }))
                  }
                />
              }
              label="Count this review as billed"
              sx={{ mt: 1 }}
            />
            <TextField
              fullWidth
              type="number"
              label="Weight Factor"
              value={reviewFormData.weight_factor}
              onChange={(e) => setReviewFormData(prev => ({ ...prev, weight_factor: parseFloat(e.target.value) || 1.0 }))}
              margin="normal"
              inputProps={{ step: 0.1 }}
            />
            <TextField
              fullWidth
              label="Disciplines"
              value={reviewFormData.disciplines}
              onChange={(e) => setReviewFormData(prev => ({ ...prev, disciplines: e.target.value }))}
              margin="normal"
            />
            <TextField
              fullWidth
              multiline
              rows={2}
              label="Deliverables"
              value={reviewFormData.deliverables}
              onChange={(e) => setReviewFormData(prev => ({ ...prev, deliverables: e.target.value }))}
              margin="normal"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseReviewDialog}>Cancel</Button>
          <Button
            onClick={handleReviewSubmit}
            variant="contained"
            disabled={createReviewMutation.isPending || updateReviewMutation.isPending}
          >
            {createReviewMutation.isPending || updateReviewMutation.isPending ? (
              <CircularProgress size={20} />
            ) : (
              selectedReview ? 'Update Review' : 'Create Review'
            )}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Item Dialog */}
      <Dialog open={itemDialogOpen} onClose={handleCloseItemDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedItem ? `Edit Item for ${selectedService?.service_name}` : `Add Item for ${selectedService?.service_name}`}
        </DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 2 }}>
            <TextField
              fullWidth
              select
              label="Item Type"
              value={itemFormData.item_type}
              onChange={(e) => setItemFormData(prev => ({ ...prev, item_type: e.target.value }))}
              margin="normal"
            >
              {ITEM_TYPES.map((type) => (
                <MenuItem key={type} value={type}>
                  {type}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              fullWidth
              label="Title"
              value={itemFormData.title}
              onChange={(e) => setItemFormData(prev => ({ ...prev, title: e.target.value }))}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Description"
              value={itemFormData.description}
              onChange={(e) => setItemFormData(prev => ({ ...prev, description: e.target.value }))}
              margin="normal"
            />
            <TextField
              fullWidth
              type="date"
              label="Due Date"
              value={itemFormData.due_date}
              onChange={(e) => setItemFormData(prev => ({ ...prev, due_date: e.target.value }))}
              margin="normal"
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              fullWidth
              select
              label="Status"
              value={itemFormData.status}
              onChange={(e) => {
                const nextStatus = e.target.value;
                setItemFormData(prev => ({
                  ...prev,
                  status: nextStatus,
                  is_billed: nextStatus === 'completed'
                    ? true
                    : (prev.status === 'completed' ? false : prev.is_billed),
                }));
              }}
              margin="normal"
            >
              {ITEM_STATUSES.map((status) => (
                <MenuItem key={status} value={status}>
                  {status}
                </MenuItem>
              ))}
            </TextField>
            <FormControlLabel
              control={
                <Checkbox
                  checked={itemFormData.is_billed}
                  onChange={(e) =>
                    setItemFormData(prev => ({
                      ...prev,
                      is_billed: e.target.checked,
                    }))
                  }
                />
              }
              label="Count this item as billed"
              sx={{ mt: 1 }}
            />
            <TextField
              fullWidth
              select
              label="Priority"
              value={itemFormData.priority}
              onChange={(e) => setItemFormData(prev => ({ ...prev, priority: e.target.value }))}
              margin="normal"
            >
              {ITEM_PRIORITIES.map((priority) => (
                <MenuItem key={priority} value={priority}>
                  {priority}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseItemDialog}>Cancel</Button>
          <Button
            onClick={handleItemSubmit}
            variant="contained"
            disabled={createItemMutation.isPending || updateItemMutation.isPending}
          >
            {createItemMutation.isPending || updateItemMutation.isPending ? (
              <CircularProgress size={20} />
            ) : (
              selectedItem ? 'Update Item' : 'Create Item'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
