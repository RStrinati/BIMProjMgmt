
console.log("✅ wireframe.js is being loaded");
const { useState, useEffect } = React;
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
} = MaterialUI;
const { createClient } = supabase;
// TODO: replace with your Supabase project credentials
const supabaseUrl = 'https://your-project.supabase.co';
const supabaseKey = 'public-anon-key';
const supabaseClient = createClient(supabaseUrl, supabaseKey);
// Fallback sample data used if the backend is not available
const sampleProjects = [
  {
    project_id: 1,
    project_name: 'Sample Project',
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    status: 'Active',
    priority: 'High',
    client_name: 'ACME Corp',
    contract_value: 100000,
    payment_terms: 'Monthly',
    client_contact: 'Jane Doe',
    contact_email: 'jane@example.com',
  },
];
function Sidebar({ active, onChange }) {
  const items = [
    { key: 'projects', label: 'Projects' },
    { key: 'bep', label: 'BEP Manager' },
    { key: 'imports', label: 'Data Imports' },
    { key: 'reviews', label: 'Review Cycles' },
    { key: 'validation', label: 'Validation' },
    { key: 'issues', label: 'Coordination Issues' },
    { key: 'kpis', label: 'KPIs & Reports' },
  ];
  return (
    <div className="sidebar">
      <h2>BIM PM</h2>
      <ul>
        {items.map(it => (
          <li key={it.key}
              className={active === it.key ? 'active' : ''}
              onClick={() => onChange(it.key)}>
            {it.label}
          </li>
        ))}
      </ul>
    </div>
  );
}
function TopBar() {
  return (
    <div className="topbar">
      <div>
        <select>
          <option>Project A</option>
          <option>Project B</option>
        </select>
      </div>
      <div>User</div>
    </div>
  );
}
function Placeholder({ title }) {
  return (
    <div>
      <h3>{title}</h3>
      <p>Content coming soon...</p>
    </div>
  );
}
function EditProject({ project, onClose }) {
  const [form, setForm] = useState({
    contract_value: project.contract_value || '',
    payment_terms: project.payment_terms || '',
    client_contact: project.client_contact || '',
    contact_email: project.contact_email || '',
  });
  const save = () => {
    fetch(`/api/projects/${project.project_id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    }).then(onClose);
  };
  return (
    <div className="modal">
      <div className="modal-content">
        <h4>Edit {project.project_name}</h4>
        <TextField label="Contract Value" fullWidth margin="dense"
          value={form.contract_value}
          onChange={e => setForm({ ...form, contract_value: e.target.value })}
        />
        <TextField label="Payment Terms" fullWidth margin="dense"
          value={form.payment_terms}
          onChange={e => setForm({ ...form, payment_terms: e.target.value })}
        />
        <TextField label="Client Contact" fullWidth margin="dense"
          value={form.client_contact}
          onChange={e => setForm({ ...form, client_contact: e.target.value })}
        />
        <TextField label="Contact Email" fullWidth margin="dense"
          value={form.contact_email}
          onChange={e => setForm({ ...form, contact_email: e.target.value })}
        />
        <div style={{ marginTop: '1rem' }}>
          <Button variant="contained" onClick={save}>Save</Button>
          <Button onClick={onClose} style={{ marginLeft: '1rem' }}>Cancel</Button>
        </div>
      </div>
    </div>
  );
}
function AddProject({ onClose }) {
  const empty = {
    project_name: '',
    client_id: '',
    project_type_id: '',
    sector_id: '',
    delivery_method_id: '',
    project_phase_id: '',
    construction_stage_id: '',
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
    priority: 'Low',
  };
  const [form, setForm] = useState(empty);
  const [options, setOptions] = useState({
    clients: [],
    project_types: [],
    sectors: [],
    delivery_methods: [],
    project_phases: [],
    construction_stages: [],
  });
  useEffect(() => {
    const tables = [
      'clients',
      'project_types',
      'sectors',
      'delivery_methods',
      'project_phases',
      'construction_stages',
    ];
    tables.forEach(t => {
      fetch(`/api/reference/${t}`)
        .then(res => res.ok ? res.json() : [])
        .then(data => setOptions(o => ({ ...o, [t]: data })))
        .catch(() => {});
    });
  }, []);
  const save = () => {
    fetch('/api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    }).then(onClose);
  };
  const handle = (k, v) => setForm(f => ({ ...f, [k]: v }));
  return (
    <div className="modal">
      <div className="modal-content" style={{ maxHeight: '80vh', overflow: 'auto' }}>
        <h4>New Project</h4>
        <TextField label="Project Name" fullWidth margin="dense" value={form.project_name}
          onChange={e => handle('project_name', e.target.value)} required />
        <FormControl fullWidth margin="dense">
          <InputLabel>Client</InputLabel>
          <Select value={form.client_id} label="Client" onChange={e => handle('client_id', e.target.value)}>
            {options.clients.map(c => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
          </Select>
        </FormControl>
        <FormControl fullWidth margin="dense">
          <InputLabel>Project Type</InputLabel>
          <Select value={form.project_type_id} label="Project Type" onChange={e => handle('project_type_id', e.target.value)}>
            {options.project_types.map(o => <MenuItem key={o.id} value={o.id}>{o.name}</MenuItem>)}
          </Select>
        </FormControl>
        <FormControl fullWidth margin="dense">
          <InputLabel>Sector</InputLabel>
          <Select value={form.sector_id} label="Sector" onChange={e => handle('sector_id', e.target.value)}>
            {options.sectors.map(o => <MenuItem key={o.id} value={o.id}>{o.name}</MenuItem>)}
          </Select>
        </FormControl>
        <FormControl fullWidth margin="dense">
          <InputLabel>Delivery Method</InputLabel>
          <Select value={form.delivery_method_id} label="Delivery Method" onChange={e => handle('delivery_method_id', e.target.value)}>
            {options.delivery_methods.map(o => <MenuItem key={o.id} value={o.id}>{o.name}</MenuItem>)}
          </Select>
        </FormControl>
        <FormControl fullWidth margin="dense">
          <InputLabel>Project Phase</InputLabel>
          <Select value={form.project_phase_id} label="Project Phase" onChange={e => handle('project_phase_id', e.target.value)}>
            {options.project_phases.map(o => <MenuItem key={o.id} value={o.id}>{o.name}</MenuItem>)}
          </Select>
        </FormControl>
        <FormControl fullWidth margin="dense">
          <InputLabel>Construction Stage</InputLabel>
          <Select value={form.construction_stage_id} label="Construction Stage" onChange={e => handle('construction_stage_id', e.target.value)}>
            {options.construction_stages.map(o => <MenuItem key={o.id} value={o.id}>{o.name}</MenuItem>)}
          </Select>
        </FormControl>
        <TextField label="Project Manager" fullWidth margin="dense" value={form.project_manager} onChange={e => handle('project_manager', e.target.value)} />
        <TextField label="Internal Lead" fullWidth margin="dense" value={form.internal_lead} onChange={e => handle('internal_lead', e.target.value)} />
        <TextField label="Contract Number" fullWidth margin="dense" value={form.contract_number} onChange={e => handle('contract_number', e.target.value)} />
        <TextField label="Contract Value" fullWidth margin="dense" value={form.contract_value} onChange={e => handle('contract_value', e.target.value)} />
        <TextField label="Agreed Fee" fullWidth margin="dense" value={form.agreed_fee} onChange={e => handle('agreed_fee', e.target.value)} />
        <TextField label="Payment Terms" fullWidth margin="dense" value={form.payment_terms} onChange={e => handle('payment_terms', e.target.value)} />
        <TextField label="Folder Path" fullWidth margin="dense" value={form.folder_path} onChange={e => handle('folder_path', e.target.value)} />
        <TextField label="IFC Folder Path" fullWidth margin="dense" value={form.ifc_folder_path} onChange={e => handle('ifc_folder_path', e.target.value)} />
        <TextField label="Data Export Folder" fullWidth margin="dense" value={form.data_export_folder} onChange={e => handle('data_export_folder', e.target.value)} />
        <TextField label="Start Date" type="date" fullWidth margin="dense" InputLabelProps={{ shrink: true }} value={form.start_date} onChange={e => handle('start_date', e.target.value)} />
        <TextField label="End Date" type="date" fullWidth margin="dense" InputLabelProps={{ shrink: true }} value={form.end_date} onChange={e => handle('end_date', e.target.value)} />
        <FormControl fullWidth margin="dense">
          <InputLabel>Status</InputLabel>
          <Select value={form.status} label="Status" onChange={e => handle('status', e.target.value)}>
            <MenuItem value="Planning">Planning</MenuItem>
            <MenuItem value="Active">Active</MenuItem>
            <MenuItem value="On Hold">On Hold</MenuItem>
            <MenuItem value="Complete">Complete</MenuItem>
          </Select>
        </FormControl>
        <FormControl fullWidth margin="dense">
          <InputLabel>Priority</InputLabel>
          <Select value={form.priority} label="Priority" onChange={e => handle('priority', e.target.value)}>
            <MenuItem value="Low">Low</MenuItem>
            <MenuItem value="Medium">Medium</MenuItem>
            <MenuItem value="High">High</MenuItem>
          </Select>
        </FormControl>
        <div style={{ marginTop: '1rem' }}>
          <Button variant="contained" onClick={save}>Create</Button>
          <Button onClick={onClose} style={{ marginLeft: '1rem' }}>Cancel</Button>
        </div>
      </div>
    </div>
  );
}
function TabPanel({ children, value, index }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <div>{children}</div>}
    </div>
  );
}
function ProjectDetail({ project, onBack }) {
  const [tab, setTab] = useState(0);
  const [details, setDetails] = useState(project);
  useEffect(() => {
    // Retrieve up-to-date project details from the backend when the
    // component mounts. Only a subset of fields may be returned so we
    // merge them with the provided project object.
    fetch(`/api/project/${project.project_id}`)
      .then(res => res.ok ? res.json() : Promise.reject())
      .then(data => setDetails(prev => ({ ...prev, ...data })))
      .catch(() => setDetails(project));
  }, [project.project_id]);
  if (!details) return null;
  return (
    <div>
      <Button variant="outlined" onClick={onBack} style={{ marginBottom: '1rem' }}>
        Back to list
      </Button>
      <h3>{details.project_name}</h3>
      <Tabs value={tab} onChange={(e, v) => setTab(v)}>
        <Tab label="Overview" />
        <Tab label="Review Schedule" />
        <Tab label="BEP Sections" />
        <Tab label="Documents" />
        <Tab label="Tasks & Issues" />
        <Tab label="Parameters" />
      </Tabs>
      <TabPanel value={tab} index={0}>
        <Box sx={{ p: 2 }}>
          <p><strong>Start:</strong> {details.start_date}</p>
          <p><strong>End:</strong> {details.end_date}</p>
          <p><strong>Status:</strong> {details.status}</p>
          <p><strong>Priority:</strong> {details.priority}</p>
        </Box>
      </TabPanel>
      <TabPanel value={tab} index={1}>
        <Box sx={{ p: 2 }}>Review schedule coming soon...</Box>
      </TabPanel>
      <TabPanel value={tab} index={2}>
        <Box sx={{ p: 2 }}>BEP sections coming soon...</Box>
      </TabPanel>
      <TabPanel value={tab} index={3}>
        <Box sx={{ p: 2 }}>Documents view coming soon...</Box>
      </TabPanel>
      <TabPanel value={tab} index={4}>
        <Box sx={{ p: 2 }}>Tasks and issues coming soon...</Box>
      </TabPanel>
      <TabPanel value={tab} index={5}>
        <Box sx={{ p: 2 }}>Parameters coming soon...</Box>
      </TabPanel>
    </div>
  );
}
function ProjectsPage() {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [selected, setSelected] = useState(null);
  const [editing, setEditing] = useState(null);
  const [adding, setAdding] = useState(false);
  const [projects, setProjects] = useState([]);
  const [editRow, setEditRow] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [refs, setRefs] = useState({
    clients: [],
    project_types: [],
    sectors: [],
    delivery_methods: [],
    project_phases: [],
    construction_stages: [],
  });
  useEffect(() => {
    // Retrieve project data from the vw_projects_full view.
    // Fallback to the bundled sample when the API is unavailable.
    fetch('/api/projects_full')
      .then(res => res.ok ? res.json() : Promise.reject())
      .then(setProjects)
      .catch(() => setProjects(sampleProjects));
  }, []);
  useEffect(() => {
    const tables = [
      'clients',
      'project_types',
      'sectors',
      'delivery_methods',
      'project_phases',
      'construction_stages',
    ];
    tables.forEach(t => {
      fetch(`/api/reference/${t}`)
        .then(res => res.ok ? res.json() : [])
        .then(data => setRefs(r => ({ ...r, [t]: data })))
        .catch(() => {});
    });
  }, []);
  const filtered = projects.filter(p => {
    const matchesSearch =
      !search ||
      p.project_name.toLowerCase().includes(search.toLowerCase()) ||
      (p.contract_number && p.contract_number.toLowerCase().includes(search.toLowerCase()));
    const matchesStatus = !status || p.status === status;
    return matchesSearch && matchesStatus;
  });
  const startEdit = (p) => {
    setEditRow(p.project_id);
    setEditForm({
      project_name: p.project_name,
      client_id: p.client_id,
      project_type_id: p.project_type_id,
      sector_id: p.sector_id,
      delivery_method_id: p.delivery_method_id,
      project_phase_id: p.project_phase_id,
      construction_stage_id: p.construction_stage_id,
      project_manager: p.project_manager,
      internal_lead: p.internal_lead,
      status: p.status,
      priority: p.priority,
    });
  };
  const saveEdit = (pid) => {
    fetch(`/api/projects/${pid}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editForm),
    }).then(() => {
      setEditRow(null);
      fetch('/api/projects_full')
        .then(res => res.ok ? res.json() : Promise.reject())
        .then(setProjects)
        .catch(() => {});
    });
  };
  if (selected) {
    return <ProjectDetail project={selected} onBack={() => setSelected(null)} />;
  }
  if (editing) {
    const refresh = () => {
      setEditing(null);
      fetch('/api/projects_full')
        .then(res => res.ok ? res.json() : Promise.reject())
        .then(setProjects)
        .catch(() => {});
    };
    return <EditProject project={editing} onClose={refresh} />;
  }
  if (adding) {
    const refresh = () => {
      setAdding(false);
      fetch('/api/projects_full')
        .then(res => res.ok ? res.json() : Promise.reject())
        .then(setProjects)
        .catch(() => {});
    };
    return <AddProject onClose={refresh} />;
  }
  return (
    <div>
      <h3>Projects</h3>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
        <TextField label="Search" size="small" value={search} onChange={e => setSearch(e.target.value)} />
        <FormControl size="small">
          <InputLabel>Status</InputLabel>
          <Select value={status} label="Status" onChange={e => setStatus(e.target.value)}>
            <MenuItem value="">All</MenuItem>
            <MenuItem value="Active">Active</MenuItem>
            <MenuItem value="Planning">Planning</MenuItem>
          </Select>
        </FormControl>
        <Button variant="contained" size="small" onClick={() => setAdding(true)}>
          New Project
        </Button>
      </div>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Project Name</TableCell>
              <TableCell>Client</TableCell>
              <TableCell>Project Type</TableCell>
              <TableCell>Sector</TableCell>
              <TableCell>Delivery Method</TableCell>
              <TableCell>Phase</TableCell>
              <TableCell>Stage</TableCell>
              <TableCell>Project Manager</TableCell>
              <TableCell>Internal Lead</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Priority</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map(p => (
              <TableRow key={p.project_id} hover>
                {editRow === p.project_id ? (
                  <>
                    <TableCell><TextField value={editForm.project_name} onChange={e=>setEditForm(f=>({...f,project_name:e.target.value}))}/></TableCell>
                    <TableCell><Select size="small" value={editForm.client_id||''} onChange={e=>setEditForm(f=>({...f,client_id:e.target.value}))}>{refs.clients.map(o=><MenuItem key={o.id} value={o.id}>{o.name}</MenuItem>)}</Select></TableCell>
                    <TableCell><Select size="small" value={editForm.project_type_id||''} onChange={e=>setEditForm(f=>({...f,project_type_id:e.target.value}))}>{refs.project_types.map(o=><MenuItem key={o.id} value={o.id}>{o.name}</MenuItem>)}</Select></TableCell>
                    <TableCell><Select size="small" value={editForm.sector_id||''} onChange={e=>setEditForm(f=>({...f,sector_id:e.target.value}))}>{refs.sectors.map(o=><MenuItem key={o.id} value={o.id}>{o.name}</MenuItem>)}</Select></TableCell>
                    <TableCell><Select size="small" value={editForm.delivery_method_id||''} onChange={e=>setEditForm(f=>({...f,delivery_method_id:e.target.value}))}>{refs.delivery_methods.map(o=><MenuItem key={o.id} value={o.id}>{o.name}</MenuItem>)}</Select></TableCell>
                    <TableCell><Select size="small" value={editForm.project_phase_id||''} onChange={e=>setEditForm(f=>({...f,project_phase_id:e.target.value}))}>{refs.project_phases.map(o=><MenuItem key={o.id} value={o.id}>{o.name}</MenuItem>)}</Select></TableCell>
                    <TableCell><Select size="small" value={editForm.construction_stage_id||''} onChange={e=>setEditForm(f=>({...f,construction_stage_id:e.target.value}))}>{refs.construction_stages.map(o=><MenuItem key={o.id} value={o.id}>{o.name}</MenuItem>)}</Select></TableCell>
                    <TableCell><TextField size="small" value={editForm.project_manager||''} onChange={e=>setEditForm(f=>({...f,project_manager:e.target.value}))}/></TableCell>
                    <TableCell><TextField size="small" value={editForm.internal_lead||''} onChange={e=>setEditForm(f=>({...f,internal_lead:e.target.value}))}/></TableCell>
                    <TableCell><Select size="small" value={editForm.status||''} onChange={e=>setEditForm(f=>({...f,status:e.target.value}))}><MenuItem value="Planning">Planning</MenuItem><MenuItem value="Active">Active</MenuItem><MenuItem value="On Hold">On Hold</MenuItem><MenuItem value="Complete">Complete</MenuItem></Select></TableCell>
                    <TableCell><Select size="small" value={editForm.priority||''} onChange={e=>setEditForm(f=>({...f,priority:e.target.value}))}><MenuItem value="Low">Low</MenuItem><MenuItem value="Medium">Medium</MenuItem><MenuItem value="High">High</MenuItem></Select></TableCell>
                    <TableCell>
                      <Button size="small" onClick={()=>saveEdit(p.project_id)}>Save</Button>
                      <Button size="small" onClick={()=>setEditRow(null)}>Cancel</Button>
                    </TableCell>
                  </>
                ) : (
                  <>
                    <TableCell onClick={() => setSelected(p)}>{p.project_name}</TableCell>
                    <TableCell>{p.client_name}</TableCell>
                    <TableCell>{p.project_type}</TableCell>
                    <TableCell>{p.sector}</TableCell>
                    <TableCell>{p.delivery_method}</TableCell>
                    <TableCell>{p.phase}</TableCell>
                    <TableCell>{p.stage}</TableCell>
                    <TableCell>{p.project_manager}</TableCell>
                    <TableCell>{p.internal_lead}</TableCell>
                    <TableCell>{p.status}</TableCell>
                    <TableCell>{p.priority}</TableCell>
                    <TableCell>
                      <Button size="small" onClick={()=>startEdit(p)}>Edit</Button>
                    </TableCell>
                  </>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}
const pages = {
  projects: ProjectsPage,
  bep: () => <Placeholder title="BEP Manager" />,
  imports: () => <Placeholder title="Data Imports" />,
  reviews: () => <Placeholder title="Review Cycles" />,
  validation: () => <Placeholder title="Validation" />,
  issues: () => <Placeholder title="Coordination Issues" />,
  kpis: () => <Placeholder title="KPIs & Reports" />,
};
function App() {
  const [page, setPage] = useState('projects');
  const Page = pages[page];
  return (
    <div className="app-container">
      <Sidebar active={page} onChange={setPage} />
      <div className="main">
        <TopBar />
        <div className="content">
          <Page />
        </div>
      </div>
    </div>
  );
}
ReactDOM.render(<App />, document.getElementById('root'));
