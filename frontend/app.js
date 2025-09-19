const { useEffect, useState, useMemo } = React;
const {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Box,
  Button,
  Grid,
  Typography,
  Chip,
  LinearProgress,
  Alert,
} = MaterialUI;

// --- Reviews Module (new) ---
function ReviewPlanningTab() {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [services, setServices] = useState([]);
  const [contextNotes, setContextNotes] = useState('Notes for design managers, discipline leads, or client feedback...');
  const [defaultStartDate, setDefaultStartDate] = useState('');
  const [defaultFrequency, setDefaultFrequency] = useState('weekly');
  const [defaultReviewCount, setDefaultReviewCount] = useState('4');

  useEffect(() => {
    fetch('/api/projects').then(r => r.ok ? r.json() : []).then(setProjects).catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    if (!projectId) { setServices([]); return; }
    fetch(`/api/project_services/${projectId}`).then(r => r.ok ? r.json() : []).then(setServices).catch(() => setServices([]));
  }, [projectId]);

  const generateReviewsFromServices = () => {
    if (!projectId) return;
    fetch(`/api/generate_reviews_from_services/${projectId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start_date: defaultStartDate,
        frequency: defaultFrequency,
        review_count: parseInt(defaultReviewCount)
      })
    })
      .then(() => {
        // Refresh services to show updated review planning
        fetch(`/api/project_services/${projectId}`).then(r => r.json()).then(setServices);
      })
      .catch(() => {});
  };

  return (
    <div>
      <h3>Review Planning & Scheduling</h3>

      {/* Project Selection */}
      <div style={{ marginBottom: '1rem' }}>
        <FormControl size="small" style={{ minWidth: 300 }}>
          <InputLabel>Project</InputLabel>
          <Select value={projectId} label="Project" onChange={e => setProjectId(e.target.value)}>
            <MenuItem value=""><em>Select Project</em></MenuItem>
            {projects.map(p => <MenuItem key={p.project_id} value={p.project_id}>{p.project_name}</MenuItem>)}
          </Select>
        </FormControl>
      </div>

      <div style={{ display: 'flex', gap: '1rem' }}>
        {/* Context Column */}
        <div style={{ flex: 1, minWidth: '250px' }}>
          <Paper style={{ padding: '1rem', marginBottom: '1rem' }}>
            <h4>Project Context</h4>
            <p style={{ fontSize: '0.9em', color: '#666', marginBottom: '1rem' }}>
              Capture key milestone notes or coordination focus areas for this review cycle.
            </p>
            <TextField
              multiline
              rows={8}
              fullWidth
              value={contextNotes}
              onChange={e => setContextNotes(e.target.value)}
              variant="outlined"
              size="small"
            />
          </Paper>

          <Paper style={{ padding: '1rem' }}>
            <h4>Cadence Defaults</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <TextField
                label="Default Start Date"
                type="date"
                value={defaultStartDate}
                onChange={e => setDefaultStartDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
                size="small"
              />
              <FormControl size="small">
                <InputLabel>Default Frequency</InputLabel>
                <Select value={defaultFrequency} label="Default Frequency" onChange={e => setDefaultFrequency(e.target.value)}>
                  <MenuItem value="weekly">Weekly</MenuItem>
                  <MenuItem value="bi-weekly">Bi-weekly</MenuItem>
                  <MenuItem value="monthly">Monthly</MenuItem>
                  <MenuItem value="as-required">As Required</MenuItem>
                </Select>
              </FormControl>
              <TextField
                label="Default Review Count"
                type="number"
                value={defaultReviewCount}
                onChange={e => setDefaultReviewCount(e.target.value)}
                size="small"
              />
            </div>
          </Paper>
        </div>

        {/* Workbench Column */}
        <div style={{ flex: 3 }}>
          <Paper style={{ padding: '1rem', marginBottom: '1rem' }}>
            <h4>Service Review Planning</h4>
            <p style={{ fontSize: '0.9em', color: '#666', fontStyle: 'italic', marginBottom: '1rem' }}>
              Services are managed in the Service Setup tab. This view shows service review planning details.
            </p>
            <Button
              variant="contained"
              size="small"
              onClick={generateReviewsFromServices}
              disabled={!projectId}
              style={{ marginBottom: '1rem' }}
            >
              Generate Reviews from Services
            </Button>

            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Service</TableCell>
                    <TableCell>Phase</TableCell>
                    <TableCell>Review Count</TableCell>
                    <TableCell>Frequency</TableCell>
                    <TableCell>Start Date</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {services.map(s => (
                    <TableRow key={s.service_id || s.id}>
                      <TableCell>{s.service_name || s.name}</TableCell>
                      <TableCell>{s.phase || 'Design'}</TableCell>
                      <TableCell>{s.review_count || defaultReviewCount}</TableCell>
                      <TableCell>{s.frequency || defaultFrequency}</TableCell>
                      <TableCell>{s.start_date || defaultStartDate}</TableCell>
                      <TableCell>{s.status || 'Planned'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </div>

        {/* Insights Column */}
        <div style={{ flex: 1, minWidth: '200px' }}>
          <Paper style={{ padding: '1rem' }}>
            <h4>Planning Insights</h4>
            <div style={{ fontSize: '0.9em', color: '#666' }}>
              <p><strong>Total Services:</strong> {services.length}</p>
              <p><strong>Active Reviews:</strong> {services.filter(s => s.status === 'Active').length}</p>
              <p><strong>Planned Reviews:</strong> {services.filter(s => s.status === 'Planned').length}</p>
              <p><strong>Completed:</strong> {services.filter(s => s.status === 'Completed').length}</p>
            </div>
          </Paper>
        </div>
      </div>
    </div>
  );
}

function ReviewExecutionTab() {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [cycleId, setCycleId] = useState('');
  const [cycles, setCycles] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [reviewSummary, setReviewSummary] = useState(null);

  useEffect(() => {
    fetch('/api/projects').then(r => r.ok ? r.json() : []).then(setProjects).catch(() => setProjects([]));
    fetch('/api/users').then(r => r.ok ? r.json() : []).then(setUsers).catch(() => setUsers([]));
  }, []);

  useEffect(() => {
    if (!projectId) {
      setCycles([]);
      setTasks([]);
      setReviewSummary(null);
      return;
    }
    fetch(`/api/cycle_ids/${projectId}`).then(r => r.ok ? r.json() : []).then(c => {
      setCycles(c);
      setCycleId(c[0] || '');
    }).catch(() => setCycles([]));
  }, [projectId]);

  useEffect(() => {
    if (!projectId || !cycleId) {
      setTasks([]);
      setReviewSummary(null);
      return;
    }
    fetch(`/api/review_tasks?project_id=${projectId}&cycle_id=${cycleId}`)
      .then(r => r.ok ? r.json() : [])
      .then(setTasks)
      .catch(() => setTasks([]));

    fetch(`/api/review_summary?project_id=${projectId}&cycle_id=${cycleId}`)
      .then(r => r.ok ? r.json() : null)
      .then(setReviewSummary)
      .catch(() => setReviewSummary(null));
  }, [projectId, cycleId]);

  const assignUser = (scheduleId, userId) => {
    fetch(`/api/review_task/${scheduleId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    })
      .then(() => {
        // Refresh tasks
        fetch(`/api/review_tasks?project_id=${projectId}&cycle_id=${cycleId}`)
          .then(r => r.json())
          .then(setTasks);
      })
      .catch(() => {});
  };

  const updateTaskStatus = (scheduleId, status) => {
    fetch(`/api/review_task/${scheduleId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: status })
    })
      .then(() => {
        // Refresh tasks and summary
        fetch(`/api/review_tasks?project_id=${projectId}&cycle_id=${cycleId}`)
          .then(r => r.json())
          .then(setTasks);
        fetch(`/api/review_summary?project_id=${projectId}&cycle_id=${cycleId}`)
          .then(r => r.json())
          .then(setReviewSummary);
      })
      .catch(() => {});
  };

  const saveFolderPath = (scheduleId, folderPath) => {
    fetch(`/api/review_task/${scheduleId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_path: folderPath })
    })
      .then(() => {
        // Refresh tasks
        fetch(`/api/review_tasks?project_id=${projectId}&cycle_id=${cycleId}`)
          .then(r => r.json())
          .then(setTasks);
      })
      .catch(() => {});
  };

  return (
    <div>
      <h3>Review Execution & Tracking</h3>

      {/* Project and Cycle Selection */}
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <FormControl size="small" style={{ minWidth: 300 }}>
          <InputLabel>Project</InputLabel>
          <Select value={projectId} label="Project" onChange={e => setProjectId(e.target.value)}>
            <MenuItem value=""><em>Select Project</em></MenuItem>
            {projects.map(p => <MenuItem key={p.project_id} value={p.project_id}>{p.project_name}</MenuItem>)}
          </Select>
        </FormControl>

        {cycles.length > 0 && (
          <FormControl size="small" style={{ minWidth: 200 }}>
            <InputLabel>Cycle</InputLabel>
            <Select value={cycleId} label="Cycle" onChange={e => setCycleId(e.target.value)}>
              {cycles.map(c => <MenuItem key={c} value={c}>{c}</MenuItem>)}
            </Select>
          </FormControl>
        )}
      </div>

      {/* Review Summary */}
      {reviewSummary && (
        <div style={{ marginBottom: '1rem', display: 'flex', gap: '2rem' }}>
          <Paper style={{ padding: '1rem', flex: 1 }}>
            <h4>Review Progress</h4>
            <div style={{ display: 'flex', gap: '1rem', fontSize: '0.9em' }}>
              <div><strong>Total Tasks:</strong> {reviewSummary.total_tasks || 0}</div>
              <div><strong>Completed:</strong> {reviewSummary.completed_tasks || 0}</div>
              <div><strong>In Progress:</strong> {reviewSummary.in_progress_tasks || 0}</div>
              <div><strong>Pending:</strong> {reviewSummary.pending_tasks || 0}</div>
            </div>
          </Paper>
          <Paper style={{ padding: '1rem', flex: 1 }}>
            <h4>Cycle Information</h4>
            <div style={{ fontSize: '0.9em' }}>
              <div><strong>Cycle:</strong> {cycleId}</div>
              <div><strong>Start Date:</strong> {reviewSummary.cycle_start || 'N/A'}</div>
              <div><strong>End Date:</strong> {reviewSummary.cycle_end || 'N/A'}</div>
            </div>
          </Paper>
        </div>
      )}

      {/* Tasks Table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Task ID</TableCell>
              <TableCell>Service</TableCell>
              <TableCell>Review Date</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Assignee</TableCell>
              <TableCell>Folder Path</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map(task => (
              <TableRow key={task.schedule_id}>
                <TableCell>{task.schedule_id}</TableCell>
                <TableCell>{task.service_name || task.service || ''}</TableCell>
                <TableCell>{task.review_date || task.planned_start || ''}</TableCell>
                <TableCell>
                  <FormControl size="small" style={{ minWidth: 120 }}>
                    <Select
                      value={task.status || 'pending'}
                      onChange={e => updateTaskStatus(task.schedule_id, e.target.value)}
                    >
                      <MenuItem value="pending">Pending</MenuItem>
                      <MenuItem value="in_progress">In Progress</MenuItem>
                      <MenuItem value="completed">Completed</MenuItem>
                      <MenuItem value="cancelled">Cancelled</MenuItem>
                    </Select>
                  </FormControl>
                </TableCell>
                <TableCell>
                  <FormControl size="small" style={{ minWidth: 150 }}>
                    <Select
                      value={task.user_id || ''}
                      onChange={e => assignUser(task.schedule_id, e.target.value)}
                      displayEmpty
                    >
                      <MenuItem value=""><em>Unassigned</em></MenuItem>
                      {users.map(u => (
                        <MenuItem key={u.user_id} value={u.user_id}>
                          {u.user_name || u.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    value={task.folder_path || ''}
                    onChange={e => saveFolderPath(task.schedule_id, e.target.value)}
                    placeholder="Enter folder path..."
                    style={{ minWidth: 200 }}
                  />
                </TableCell>
                <TableCell>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => saveFolderPath(task.schedule_id, task.folder_path || '')}
                  >
                    Save
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}

function ServiceSetupTab() {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [services, setServices] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');

  useEffect(() => {
    fetch('/api/projects').then(r => r.ok ? r.json() : []).then(setProjects).catch(() => setProjects([]));
    fetch('/api/service_templates').then(r => r.ok ? r.json() : []).then(setTemplates).catch(() => setTemplates([]));
  }, []);

  useEffect(() => {
    if (!projectId) { setServices([]); return; }
    fetch(`/api/project_services/${projectId}`).then(r => r.ok ? r.json() : []).then(setServices).catch(() => setServices([]));
  }, [projectId]);

  const loadTemplate = () => {
    if (!selectedTemplate) return;
    fetch(`/api/service_template/${selectedTemplate}`)
      .then(r => r.ok ? r.json() : [])
      .then(templateServices => {
        // Show preview of services that would be added
        console.log('Template services:', templateServices);
      })
      .catch(() => {});
  };

  const applyTemplate = () => {
    if (!projectId || !selectedTemplate) return;
    fetch(`/api/apply_service_template`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, template_id: selectedTemplate })
    })
      .then(() => {
        fetch(`/api/project_services/${projectId}`).then(r => r.json()).then(setServices);
      })
      .catch(() => {});
  };

  const clearServices = () => {
    if (!projectId) return;
    if (!confirm('Are you sure you want to clear all services for this project?')) return;
    fetch(`/api/clear_project_services/${projectId}`, { method: 'DELETE' })
      .then(() => setServices([]))
      .catch(() => {});
  };

  const addService = () => {
    const serviceName = prompt('Enter service name:');
    if (!serviceName || !projectId) return;

    fetch('/api/project_services', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: projectId,
        service_name: serviceName,
        phase: 'Design',
        service_code: serviceName.substring(0, 3).toUpperCase(),
        unit_type: 'LS',
        quantity: 1,
        rate: 0,
        status: 'Active'
      })
    })
      .then(() => {
        fetch(`/api/project_services/${projectId}`)
          .then(r => r.json())
          .then(setServices);
      })
      .catch(() => {});
  };

  return (
    <div>
      <h3>Service Setup & Templates</h3>

      {/* Project Selection */}
      <div style={{ marginBottom: '1rem' }}>
        <FormControl size="small" style={{ minWidth: 300 }}>
          <InputLabel>Project</InputLabel>
          <Select value={projectId} label="Project" onChange={e => setProjectId(e.target.value)}>
            <MenuItem value=""><em>Select Project</em></MenuItem>
            {projects.map(p => <MenuItem key={p.project_id} value={p.project_id}>{p.project_name}</MenuItem>)}
          </Select>
        </FormControl>
      </div>

      {/* Service Templates */}
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <FormControl size="small" style={{ minWidth: 250 }}>
          <InputLabel>Available Templates</InputLabel>
          <Select value={selectedTemplate} label="Available Templates" onChange={e => setSelectedTemplate(e.target.value)}>
            <MenuItem value=""><em>Select Template</em></MenuItem>
            {templates.map(t => <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>)}
          </Select>
        </FormControl>
        <Button variant="outlined" size="small" onClick={loadTemplate}>Load Template</Button>
        <Button variant="contained" size="small" onClick={applyTemplate} disabled={!projectId || !selectedTemplate}>Apply to Project</Button>
        <Button variant="outlined" size="small" color="error" onClick={clearServices} disabled={!projectId}>Clear All Services</Button>
      </div>

      {/* Current Project Services */}
      <div style={{ marginBottom: '1rem' }}>
        <Button variant="contained" size="small" onClick={addService} disabled={!projectId}>Add Service</Button>
      </div>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Service ID</TableCell>
              <TableCell>Phase</TableCell>
              <TableCell>Service Code</TableCell>
              <TableCell>Service Name</TableCell>
              <TableCell>Unit Type</TableCell>
              <TableCell>Qty</TableCell>
              <TableCell>Rate</TableCell>
              <TableCell>Fee</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Start</TableCell>
              <TableCell>End</TableCell>
              <TableCell>Frequency</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {services.map(s => (
              <TableRow key={s.service_id || s.id}>
                <TableCell>{s.service_id || s.id}</TableCell>
                <TableCell>{s.phase || 'Design'}</TableCell>
                <TableCell>{s.service_code || ''}</TableCell>
                <TableCell>{s.service_name || s.name}</TableCell>
                <TableCell>{s.unit_type || 'LS'}</TableCell>
                <TableCell>{s.quantity || 1}</TableCell>
                <TableCell>${s.rate || 0}</TableCell>
                <TableCell>${s.fee || 0}</TableCell>
                <TableCell>{s.status || 'Active'}</TableCell>
                <TableCell>{s.start_date || ''}</TableCell>
                <TableCell>{s.end_date || ''}</TableCell>
                <TableCell>{s.frequency || 'monthly'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}

function BillingProgressTab() {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [billingData, setBillingData] = useState([]);
  const [progressData, setProgressData] = useState([]);
  const [financialSummary, setFinancialSummary] = useState(null);

  useEffect(() => {
    fetch('/api/projects').then(r => r.ok ? r.json() : []).then(setProjects).catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    if (!projectId) {
      setBillingData([]);
      setProgressData([]);
      setFinancialSummary(null);
      return;
    }

    // Fetch billing data
    fetch(`/api/project_billing/${projectId}`)
      .then(r => r.ok ? r.json() : [])
      .then(setBillingData)
      .catch(() => setBillingData([]));

    // Fetch progress data
    fetch(`/api/project_progress/${projectId}`)
      .then(r => r.ok ? r.json() : [])
      .then(setProgressData)
      .catch(() => setProgressData([]));

    // Fetch financial summary
    fetch(`/api/project_financial_summary/${projectId}`)
      .then(r => r.ok ? r.json() : null)
      .then(setFinancialSummary)
      .catch(() => setFinancialSummary(null));
  }, [projectId]);

  const generateInvoice = (serviceId) => {
    fetch(`/api/generate_invoice/${serviceId}`, { method: 'POST' })
      .then(() => {
        // Refresh billing data
        fetch(`/api/project_billing/${projectId}`).then(r => r.json()).then(setBillingData);
        fetch(`/api/project_financial_summary/${projectId}`).then(r => r.json()).then(setFinancialSummary);
      })
      .catch(() => {});
  };

  const markServiceComplete = (serviceId) => {
    fetch(`/api/service_complete/${serviceId}`, { method: 'PATCH' })
      .then(() => {
        // Refresh data
        fetch(`/api/project_billing/${projectId}`).then(r => r.json()).then(setBillingData);
        fetch(`/api/project_progress/${projectId}`).then(r => r.json()).then(setProgressData);
        fetch(`/api/project_financial_summary/${projectId}`).then(r => r.json()).then(setFinancialSummary);
      })
      .catch(() => {});
  };

  return (
    <div>
      <h3>Billing & Progress</h3>

      {/* Project Selection */}
      <div style={{ marginBottom: '1rem' }}>
        <FormControl size="small" style={{ minWidth: 300 }}>
          <InputLabel>Project</InputLabel>
          <Select value={projectId} label="Project" onChange={e => setProjectId(e.target.value)}>
            <MenuItem value=""><em>Select Project</em></MenuItem>
            {projects.map(p => <MenuItem key={p.project_id} value={p.project_id}>{p.project_name}</MenuItem>)}
          </Select>
        </FormControl>
      </div>

      {/* Financial Summary */}
      {financialSummary && (
        <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem' }}>
          <Paper style={{ padding: '1rem', flex: 1 }}>
            <h4>Financial Summary</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.9em' }}>
              <div><strong>Total Contract Value:</strong></div>
              <div>${financialSummary.total_contract_value || 0}</div>
              <div><strong>Total Billed:</strong></div>
              <div>${financialSummary.total_billed || 0}</div>
              <div><strong>Outstanding:</strong></div>
              <div>${financialSummary.outstanding_amount || 0}</div>
              <div><strong>Progress (%):</strong></div>
              <div>{financialSummary.overall_progress || 0}%</div>
            </div>
          </Paper>
          <Paper style={{ padding: '1rem', flex: 1 }}>
            <h4>Progress Overview</h4>
            <div style={{ fontSize: '0.9em' }}>
              <div><strong>Services Completed:</strong> {financialSummary.completed_services || 0} / {financialSummary.total_services || 0}</div>
              <div><strong>Reviews Completed:</strong> {financialSummary.completed_reviews || 0} / {financialSummary.total_reviews || 0}</div>
              <div><strong>Invoices Generated:</strong> {financialSummary.total_invoices || 0}</div>
              <div><strong>Pending Invoices:</strong> {financialSummary.pending_invoices || 0}</div>
            </div>
          </Paper>
        </div>
      )}

      <div style={{ display: 'flex', gap: '1rem' }}>
        {/* Billing Table */}
        <div style={{ flex: 1 }}>
          <Paper style={{ padding: '1rem' }}>
            <h4>Service Billing</h4>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Service</TableCell>
                    <TableCell>Value</TableCell>
                    <TableCell>Billed</TableCell>
                    <TableCell>Outstanding</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {billingData.map(item => (
                    <TableRow key={item.service_id}>
                      <TableCell>{item.service_name}</TableCell>
                      <TableCell>${item.contract_value || 0}</TableCell>
                      <TableCell>${item.amount_billed || 0}</TableCell>
                      <TableCell>${item.outstanding || 0}</TableCell>
                      <TableCell>{item.billing_status || 'Pending'}</TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => generateInvoice(item.service_id)}
                          disabled={item.billing_status === 'Completed'}
                        >
                          Invoice
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </div>

        {/* Progress Table */}
        <div style={{ flex: 1 }}>
          <Paper style={{ padding: '1rem' }}>
            <h4>Service Progress</h4>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Service</TableCell>
                    <TableCell>Progress (%)</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Reviews</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {progressData.map(item => (
                    <TableRow key={item.service_id}>
                      <TableCell>{item.service_name}</TableCell>
                      <TableCell>{item.progress_percentage || 0}%</TableCell>
                      <TableCell>{item.status}</TableCell>
                      <TableCell>{item.completed_reviews || 0} / {item.total_reviews || 0}</TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => markServiceComplete(item.service_id)}
                          disabled={item.status === 'Completed'}
                        >
                          Complete
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </div>
      </div>
    </div>
  );
}

function ProjectBookmarksTab({ projectId }) {
  const [bookmarks, setBookmarks] = React.useState([]);
  const [title, setTitle] = React.useState("");
  const [url, setUrl] = React.useState("");
  const [desc, setDesc] = React.useState("");

  React.useEffect(() => {
    if (projectId) {
      fetch(`/api/project/${projectId}/bookmarks`)
        .then(res => res.json())
        .then(setBookmarks);
    } else {
      setBookmarks([]);
    }
  }, [projectId]);

  const addBookmark = () => {
    if (!title || !url) return;
    fetch(`/api/project/${projectId}/bookmarks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, url, description: desc })
    })
      .then(res => res.json())
      .then(result => {
        if (result.success) {
          setTitle("");
          setUrl("");
          setDesc("");
          fetch(`/api/project/${projectId}/bookmarks`)
            .then(res => res.json())
            .then(setBookmarks);
        }
      });
  };

  const deleteBookmark = (bookmarkId) => {
    fetch(`/api/project/${projectId}/bookmarks/${bookmarkId}`, {
      method: "DELETE"
    })
      .then(res => res.json())
      .then(result => {
        if (result.success) {
          setBookmarks(bookmarks.filter(b => b.bookmark_id !== bookmarkId));
        }
      });
  };

  return (
    <div>
      <h3>Project Bookmarks</h3>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Title" style={{ width: 120 }} />
        <input value={url} onChange={e => setUrl(e.target.value)} placeholder="URL" style={{ width: 220 }} />
        <input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Description" style={{ width: 140 }} />
        <button onClick={addBookmark}>Add</button>
      </div>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>URL</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {bookmarks.map(b => (
              <TableRow key={b.bookmark_id}>
                <TableCell>{b.title}</TableCell>
                <TableCell><a href={b.url} target="_blank" rel="noopener noreferrer">{b.url}</a></TableCell>
                <TableCell>{b.description}</TableCell>
                <TableCell>{b.created_at}</TableCell>
                <TableCell><button onClick={() => deleteBookmark(b.bookmark_id)}>Delete</button></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}

function ReviewsPage() {
  const [tab, setTab] = useState(0);
  return (
    <div>
      <Tabs value={tab} onChange={(e, v) => setTab(v)}>
        <Tab label="Service Setup" />
        <Tab label="Review Planning" />
        <Tab label="Review Execution & Tracking" />
        <Tab label="Billing & Progress" />
      </Tabs>
      <Box sx={{ p: 2 }}>
        {tab === 0 && <ServiceSetupTab />}
        {tab === 1 && <ReviewPlanningTab />}
        {tab === 2 && <ReviewExecutionTab />}
        {tab === 3 && <BillingProgressTab />}
      </Box>
    </div>
  );
}



function ProjectsView() {
  const empty = {
    project_name: '',
    client_id: '',
    type_id: '',
    sector_id: '',
    method_id: '',
    phase_id: '',
    stage_id: '',
    project_manager: '',
    internal_lead: '',
    contract_number: '',
    contract_value: '',
    agreed_fee: '',
    payment_terms: '',
    folder_path: '',
    ifc_folder_path: '',
    data_export_folder: '',
    start_date: '',
    end_date: '',
    status: 'Planning',
    priority: 'Low'
  };

  const [projects, setProjects] = useState([]);
  const [form, setForm] = useState(empty);
  const [showForm, setShowForm] = useState(false);
  const [refs, setRefs] = useState({});
  const [tab, setTab] = useState(0);

  const refresh = () => {
    fetch('/api/projects').then(res => res.json()).then(setProjects);
  };

  const loadRefs = () => {
    const tables = ['clients', 'project_types', 'sectors', 'delivery_methods', 'project_phases', 'construction_stages'];
    tables.forEach(t => {
      fetch(`/api/reference/${t}`)
        .then(res => res.json())
        .then(opts => setRefs(r => ({ ...r, [t]: opts })));
    });
  };

  useEffect(() => {
    refresh();
    loadRefs();
  }, []);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const createProject = () => {
    fetch('/api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    }).then(() => {
      setForm(empty);
      setShowForm(false);
      refresh();
    });
  };

  const updateProject = (id, field, value) => {
    fetch(`/api/projects/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [field]: value })
    }).then(refresh);
  };

  const renderSelect = (value, options, onChange) => (
    <select value={value || ''} onChange={e => onChange(e.target.value)}>
      <option value=""></option>
      {options.map(o => (
        <option key={o.id || o.name} value={o.id || o.name}>{o.name}</option>
      ))}
    </select>
  );

  const selectedProjectId = form.project_id || (projects[0] && projects[0].project_id);

  return (
    <div>
      <Tabs value={tab} onChange={(e, v) => setTab(v)}>
        <Tab label="Project Details" />
        <Tab label="Bookmarks" />
        <Tab label="Service Setup" />
        <Tab label="Review Planning" />
        <Tab label="Review Execution & Tracking" />
        <Tab label="Billing & Progress" />
      </Tabs>
      <Box sx={{ p: 2 }}>
        {tab === 0 && (
          <div>
            <button onClick={() => setShowForm(!showForm)}>New Project</button>
            {showForm && (
              <div className="new-project-form" style={{ marginTop: '10px' }}>
                <input placeholder="Project Name" name="project_name" value={form.project_name} onChange={handleChange} />
                {renderSelect(form.client_id, refs.clients || [], v => setForm({ ...form, client_id: v }))}
                {renderSelect(form.type_id, refs.project_types || [], v => setForm({ ...form, type_id: v }))}
                {renderSelect(form.sector_id, refs.sectors || [], v => setForm({ ...form, sector_id: v }))}
                {renderSelect(form.method_id, refs.delivery_methods || [], v => setForm({ ...form, method_id: v }))}
                {renderSelect(form.phase_id, refs.project_phases || [], v => setForm({ ...form, phase_id: v }))}
                {renderSelect(form.stage_id, refs.construction_stages || [], v => setForm({ ...form, stage_id: v }))}
                <input placeholder="Project Manager" name="project_manager" value={form.project_manager} onChange={handleChange} />
                <input placeholder="Internal Lead" name="internal_lead" value={form.internal_lead} onChange={handleChange} />
                <input placeholder="Contract Number" name="contract_number" value={form.contract_number} onChange={handleChange} />
                <input placeholder="Contract Value" name="contract_value" value={form.contract_value} onChange={handleChange} />
                <input placeholder="Agreed Fee" name="agreed_fee" value={form.agreed_fee} onChange={handleChange} />
                <input placeholder="Payment Terms" name="payment_terms" value={form.payment_terms} onChange={handleChange} />
                <input placeholder="Folder Path" name="folder_path" value={form.folder_path} onChange={handleChange} />
                <input placeholder="IFC Folder Path" name="ifc_folder_path" value={form.ifc_folder_path} onChange={handleChange} />
                <input placeholder="Data Export Folder" name="data_export_folder" value={form.data_export_folder} onChange={handleChange} />
                <input type="date" name="start_date" value={form.start_date} onChange={handleChange} />
                <input type="date" name="end_date" value={form.end_date} onChange={handleChange} />
                {renderSelect(form.status, [{ name: 'Planning' }, { name: 'Active' }, { name: 'On Hold' }, { name: 'Complete' }], v => setForm({ ...form, status: v }))}
                {renderSelect(form.priority, [{ name: 'Low' }, { name: 'Medium' }, { name: 'High' }], v => setForm({ ...form, priority: v }))}
                <button onClick={createProject}>Save</button>
              </div>
            )}

            <table border="1" cellPadding="4" style={{ marginTop: '10px' }}>
              <thead>
                <tr>
                  <th>Project Name</th>
                  <th>Client</th>
                  <th>Project Type</th>
                  <th>Sector</th>
                  <th>Delivery Method</th>
                  <th>Phase</th>
                  <th>Stage</th>
                  <th>Project Manager</th>
                  <th>Internal Lead</th>
                  <th>Status</th>
                  <th>Priority</th>
                </tr>
              </thead>
              <tbody>
                {projects.map(p => (
                  <tr key={p.project_id}>
                    <td><input value={p.project_name || ''} onChange={e => updateProject(p.project_id, 'project_name', e.target.value)} /></td>
                    <td>{renderSelect(p.client_id, refs.clients || [], v => updateProject(p.project_id, 'client_id', v))}</td>
                    <td>{renderSelect(p.type_id, refs.project_types || [], v => updateProject(p.project_id, 'type_id', v))}</td>
                    <td>{renderSelect(p.sector_id, refs.sectors || [], v => updateProject(p.project_id, 'sector_id', v))}</td>
                    <td>{renderSelect(p.method_id, refs.delivery_methods || [], v => updateProject(p.project_id, 'method_id', v))}</td>
                    <td>{renderSelect(p.phase_id, refs.project_phases || [], v => updateProject(p.project_id, 'phase_id', v))}</td>
                    <td>{renderSelect(p.stage_id, refs.construction_stages || [], v => updateProject(p.project_id, 'stage_id', v))}</td>
                    <td><input value={p.project_manager || ''} onChange={e => updateProject(p.project_id, 'project_manager', e.target.value)} /></td>
                    <td><input value={p.internal_lead || ''} onChange={e => updateProject(p.project_id, 'internal_lead', e.target.value)} /></td>
                    <td>{renderSelect(p.status, [{ name: 'Planning' }, { name: 'Active' }, { name: 'On Hold' }, { name: 'Complete' }], v => updateProject(p.project_id, 'status', v))}</td>
                    <td>{renderSelect(p.priority, [{ name: 'Low' }, { name: 'Medium' }, { name: 'High' }], v => updateProject(p.project_id, 'priority', v))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {tab === 1 && <ProjectBookmarksTab projectId={selectedProjectId} />}
        {tab === 2 && <ServiceSetupTab />}
        {tab === 3 && <ReviewPlanningTab />}
        {tab === 4 && <ReviewExecutionTab />}
        {tab === 5 && <BillingProgressTab />}
      </Box>
    </div>
  );
}


function TaskManagementView() {
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [tasks, setTasks] = useState([]);
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Task form state
  const [openDialog, setOpenDialog] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [taskForm, setTaskForm] = useState({
    task_name: '',
    project_id: '',
    priority: 'Medium',
    status: 'Not Started',
    assigned_to: '',
    start_date: '',
    end_date: '',
    estimated_hours: '',
    description: '',
  });

  useEffect(() => {
    fetch('/api/projects').then(r => r.ok ? r.json() : []).then(setProjects).catch(() => setProjects([]));
    fetch('/api/resources').then(r => r.ok ? r.json() : []).then(setResources).catch(() => setResources([]));
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadTasks(selectedProjectId);
    }
  }, [selectedProjectId]);

  const loadTasks = async (projectId) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/tasks?project_id=${projectId}`);
      if (response.ok) {
        const tasksData = await response.json();
        setTasks(tasksData);
      }
    } catch (err) {
      setError('Failed to load tasks');
      console.error('Error loading tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitTask = async () => {
    try {
      if (!taskForm.task_name.trim()) {
        setError('Task name is required');
        return;
      }

      if (!selectedProjectId) {
        setError('Please select a project');
        return;
      }

      const taskData = {
        ...taskForm,
        project_id: selectedProjectId,
      };

      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData),
      });

      if (response.ok) {
        setSuccess('Task created successfully');
        setTaskForm({
          task_name: '',
          project_id: '',
          priority: 'Medium',
          status: 'Not Started',
          assigned_to: '',
          start_date: '',
          end_date: '',
          estimated_hours: '',
          description: '',
        });
        loadTasks(selectedProjectId);
      } else {
        setError('Failed to create task');
      }
    } catch (err) {
      setError('Failed to create task');
      console.error('Error creating task:', err);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Completed': return 'success';
      case 'In Progress': return 'info';
      case 'On Hold': return 'warning';
      case 'Not Started': return 'default';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'Critical': 
      case 'High': return 'error';
      case 'Medium': return 'warning';
      case 'Low': return 'success';
      default: return 'default';
    }
  };

  return (
    <div>
      <Typography variant="h4" gutterBottom>Task Management</Typography>
      
      {/* Project Selection */}
      <Paper style={{ padding: '1rem', marginBottom: '1rem' }}>
        <FormControl fullWidth style={{ marginBottom: '1rem' }}>
          <InputLabel>Select Project</InputLabel>
          <Select
            value={selectedProjectId}
            onChange={e => setSelectedProjectId(e.target.value)}
            label="Select Project"
          >
            {projects.map(project => (
              <MenuItem key={project.project_id || project.id} value={project.project_id || project.id}>
                {project.project_name || project.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Paper>

      {/* Task Creation Form */}
      {selectedProjectId && (
        <Paper style={{ padding: '1rem', marginBottom: '1rem' }}>
          <Typography variant="h6" gutterBottom>Create New Task</Typography>
          
          {error && <Alert severity="error" style={{ marginBottom: '1rem' }}>{error}</Alert>}
          {success && <Alert severity="success" style={{ marginBottom: '1rem' }}>{success}</Alert>}
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Task Name"
                value={taskForm.task_name}
                onChange={e => setTaskForm(prev => ({ ...prev, task_name: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={taskForm.priority}
                  onChange={e => setTaskForm(prev => ({ ...prev, priority: e.target.value }))}
                  label="Priority"
                >
                  <MenuItem value="Low">Low</MenuItem>
                  <MenuItem value="Medium">Medium</MenuItem>
                  <MenuItem value="High">High</MenuItem>
                  <MenuItem value="Critical">Critical</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={taskForm.status}
                  onChange={e => setTaskForm(prev => ({ ...prev, status: e.target.value }))}
                  label="Status"
                >
                  <MenuItem value="Not Started">Not Started</MenuItem>
                  <MenuItem value="In Progress">In Progress</MenuItem>
                  <MenuItem value="On Hold">On Hold</MenuItem>
                  <MenuItem value="Completed">Completed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Assigned To</InputLabel>
                <Select
                  value={taskForm.assigned_to}
                  onChange={e => setTaskForm(prev => ({ ...prev, assigned_to: e.target.value }))}
                  label="Assigned To"
                >
                  <MenuItem value="">Unassigned</MenuItem>
                  {resources.map(resource => (
                    <MenuItem key={resource.user_id} value={resource.name}>
                      {resource.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Start Date"
                type="date"
                value={taskForm.start_date}
                onChange={e => setTaskForm(prev => ({ ...prev, start_date: e.target.value }))}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="End Date"
                type="date"
                value={taskForm.end_date}
                onChange={e => setTaskForm(prev => ({ ...prev, end_date: e.target.value }))}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={taskForm.description}
                onChange={e => setTaskForm(prev => ({ ...prev, description: e.target.value }))}
                multiline
                rows={3}
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={handleSubmitTask}
              >
                Create Task
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Task List */}
      {selectedProjectId && (
        <Paper style={{ padding: '1rem' }}>
          <Typography variant="h6" gutterBottom>Project Tasks</Typography>
          
          {loading && <LinearProgress style={{ marginBottom: '1rem' }} />}
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Task Name</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Assigned To</TableCell>
                  <TableCell>Due Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tasks.map(task => (
                  <TableRow key={task.task_id}>
                    <TableCell>
                      <Typography variant="body2" style={{ fontWeight: 'bold' }}>
                        {task.task_name}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {task.description}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={task.priority}
                        color={getPriorityColor(task.priority)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={task.status}
                        color={getStatusColor(task.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Box style={{ minWidth: 100 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={task.progress_percentage || 0} 
                          style={{ marginBottom: '0.25rem' }}
                        />
                        <Typography variant="caption">
                          {task.progress_percentage || 0}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{task.assigned_to || 'Unassigned'}</TableCell>
                    <TableCell>
                      {task.end_date ? new Date(task.end_date).toLocaleDateString() : '-'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}
    </div>
  );
}


function App() {
  const [view, setView] = useState('reviews');
  return (
    <div>
      <div style={{ marginBottom:'1rem' }}>
        <Button size="small" variant={view==='reviews'?'contained':'outlined'} onClick={()=>setView('reviews')}>Reviews</Button>
        <Button size="small" variant={view==='projects'?'contained':'outlined'} onClick={()=>setView('projects')} style={{ marginLeft: 8 }}>Projects</Button>
        <Button size="small" variant={view==='tasks'?'contained':'outlined'} onClick={()=>setView('tasks')} style={{ marginLeft: 8 }}>Tasks</Button>
      </div>
      {view === 'reviews' ? <ReviewsPage /> : 
       view === 'projects' ? <ProjectsView /> :
       view === 'tasks' ? <TaskManagementView /> : <ReviewsPage />}
    </div>
  );
}

ReactDOM.render(<App />, document.getElementById('root'));
