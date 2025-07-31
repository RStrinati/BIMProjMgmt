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

// Sample project data used until backend integration is complete
const sampleProjects = [
  {
    project_id: 1,
    project_name: 'HQ Revamp',
    client: 'Acme Corp',
    project_type: 'Office',
    delivery_method: 'Design-Build',
    contract_value: '$1,000,000',
    contract_number: 'CN001',
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    status: 'Active',
    priority: 'High',
  },
  {
    project_id: 2,
    project_name: 'New Warehouse',
    client: 'LogiTrans',
    project_type: 'Industrial',
    delivery_method: 'CM at Risk',
    contract_value: '$2,500,000',
    contract_number: 'CN002',
    start_date: '2023-06-15',
    end_date: '2024-05-30',
    status: 'Planning',
    priority: 'Medium',
  },
  {
    project_id: 3,
    project_name: 'City Library',
    client: 'Municipality',
    project_type: 'Civic',
    delivery_method: 'Design-Bid-Build',
    contract_value: '$3,300,000',
    contract_number: 'CN003',
    start_date: '2024-02-01',
    end_date: '2025-02-01',
    status: 'Active',
    priority: 'High',
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

function TabPanel({ children, value, index }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <div>{children}</div>}
    </div>
  );
}

function ProjectDetail({ project, onBack }) {
  const [tab, setTab] = useState(0);
  return (
    <div>
      <Button variant="outlined" onClick={onBack} style={{ marginBottom: '1rem' }}>
        Back to list
      </Button>
      <h3>{project.project_name}</h3>
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
          <p><strong>Client:</strong> {project.client}</p>
          <p><strong>Type:</strong> {project.project_type}</p>
          <p><strong>Delivery:</strong> {project.delivery_method}</p>
          <p><strong>Contract Value:</strong> {project.contract_value}</p>
          <p><strong>Start:</strong> {project.start_date}</p>
          <p><strong>End:</strong> {project.end_date}</p>
          <p><strong>Status:</strong> {project.status}</p>
          <p><strong>Priority:</strong> {project.priority}</p>
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
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    // Replace with API call in the future
    setProjects(sampleProjects);
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
              <TableCell>Type</TableCell>
              <TableCell>Method</TableCell>
              <TableCell>Contract Value</TableCell>
              <TableCell>Start</TableCell>
              <TableCell>End</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Priority</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map(p => (
              <TableRow key={p.project_id} hover style={{ cursor: 'pointer' }} onClick={() => setSelected(p)}>
                <TableCell>{p.project_name}</TableCell>
                <TableCell>{p.client}</TableCell>
                <TableCell>{p.project_type}</TableCell>
                <TableCell>{p.delivery_method}</TableCell>
                <TableCell>{p.contract_value}</TableCell>
                <TableCell>{p.start_date}</TableCell>
                <TableCell>{p.end_date}</TableCell>
                <TableCell>{p.status}</TableCell>
                <TableCell>{p.priority}</TableCell>
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
