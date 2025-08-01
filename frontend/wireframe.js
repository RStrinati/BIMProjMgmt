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
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    // Retrieve project data from the vw_projects_full view.
    // Fallback to the bundled sample when the API is unavailable.
    fetch('/api/projects_full')
      .then(res => res.ok ? res.json() : Promise.reject())
      .then(setProjects)
      .catch(() => setProjects(sampleProjects));
  }, []);

  const filtered = projects.filter(p => {
    const matchesSearch =
      !search ||
      p.project_name.toLowerCase().includes(search.toLowerCase()) ||
      (p.contract_number && p.contract_number.toLowerCase().includes(search.toLowerCase()));
    const matchesStatus = !status || p.status === status;
    return matchesSearch && matchesStatus;
  });

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
      </div>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Client</TableCell>
              <TableCell>Contract Value</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map(p => (
              <TableRow key={p.project_id} hover>
                <TableCell onClick={() => setSelected(p)}>{p.project_name}</TableCell>
                <TableCell>{p.client_name}</TableCell>
                <TableCell>{p.contract_value}</TableCell>
                <TableCell>
                  <Button size="small" onClick={() => setEditing(p)}>Edit</Button>
                </TableCell>
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
