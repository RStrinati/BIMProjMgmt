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
} = MaterialUI;

// --- Reviews Module (new) ---
function ReviewsPlanning() {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [stages, setStages] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [form, setForm] = useState({ stage: '', start: '', end: '', reviews: 4, frequency: 'weekly' });

  useEffect(() => {
    fetch('/api/projects').then(r=>r.ok?r.json():[]).then(setProjects).catch(()=>setProjects([]));
  }, []);

  useEffect(() => {
    if (!projectId) { setStages([]); setCycles([]); return; }
    fetch(`/api/project_services/${projectId}`).then(r=>r.ok?r.json():[]).then(setStages).catch(()=>setStages([]));
    fetch(`/api/reviews/${projectId}`).then(r=>r.ok?r.json():[]).then(setCycles).catch(()=>setCycles([]));
  }, [projectId]);

  const addStage = () => {
    if (!projectId || !form.stage || !form.start || !form.end) return;
    // POST to backend (placeholder)
    fetch('/api/stages', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ ...form, project_id: projectId }) })
      .then(()=> fetch(`/api/project_services/${projectId}`).then(r=>r.json()).then(setStages))
      .catch(()=>{});
  };

  const generateCycles = () => {
    if (!projectId) return;
    fetch(`/api/generate_review_cycles/${projectId}`, { method: 'POST' })
      .then(()=> fetch(`/api/reviews/${projectId}`).then(r=>r.json()).then(setCycles))
      .catch(()=>{});
  };

  return (
    <div>
      <h3>Reviews • Planning</h3>
      <div style={{ display:'flex', gap:'1rem', alignItems:'center' }}>
        <FormControl size="small">
          <InputLabel>Project</InputLabel>
          <Select value={projectId} label="Project" onChange={e=>setProjectId(e.target.value)} style={{ minWidth: 240 }}>
            {projects.map(p=> <MenuItem key={p.project_id} value={p.project_id}>{p.project_name}</MenuItem>)}
          </Select>
        </FormControl>
        <TextField size="small" label="Stage Name" value={form.stage} onChange={e=>setForm(f=>({...f, stage:e.target.value}))} />
        <TextField size="small" label="Start" type="date" InputLabelProps={{shrink:true}} value={form.start} onChange={e=>setForm(f=>({...f, start:e.target.value}))} />
        <TextField size="small" label="End" type="date" InputLabelProps={{shrink:true}} value={form.end} onChange={e=>setForm(f=>({...f, end:e.target.value}))} />
        <TextField size="small" label="# Reviews" type="number" value={form.reviews} onChange={e=>setForm(f=>({...f, reviews:e.target.value}))} />
        <FormControl size="small">
          <InputLabel>Frequency</InputLabel>
          <Select value={form.frequency} label="Frequency" onChange={e=>setForm(f=>({...f, frequency:e.target.value}))}>
            <MenuItem value="weekly">Weekly</MenuItem>
            <MenuItem value="bi-weekly">Bi-weekly</MenuItem>
            <MenuItem value="monthly">Monthly</MenuItem>
            <MenuItem value="milestone-based">Milestone-based</MenuItem>
          </Select>
        </FormControl>
        <Button variant="contained" size="small" onClick={addStage}>Add Stage</Button>
        <Button variant="outlined" size="small" onClick={generateCycles}>Generate Cycles</Button>
      </div>

      <h4 style={{ marginTop:'1rem' }}>Stages</h4>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead><TableRow>
            <TableCell>Stage</TableCell><TableCell>Start</TableCell><TableCell>End</TableCell><TableCell>Reviews</TableCell><TableCell>Frequency</TableCell>
          </TableRow></TableHead>
          <TableBody>
            {stages.map(s=> (
              <TableRow key={s.id || s.stage}>
                <TableCell>{s.stage || s.service_name}</TableCell>
                <TableCell>{s.start || s.start_date}</TableCell>
                <TableCell>{s.end || s.end_date}</TableCell>
                <TableCell>{s.reviews || s.num_reviews}</TableCell>
                <TableCell>{s.frequency || s.frequency_type}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <h4 style={{ marginTop:'1rem' }}>Review Cycles</h4>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead><TableRow>
            <TableCell>ID</TableCell><TableCell>Stage</TableCell><TableCell>Start</TableCell><TableCell>End</TableCell><TableCell>Reviews</TableCell>
          </TableRow></TableHead>
          <TableBody>
            {cycles.map(c=> (
              <TableRow key={c.review_cycle_id}>
                <TableCell>{c.review_cycle_id}</TableCell>
                <TableCell>{c.stage_id}</TableCell>
                <TableCell>{c.start_date}</TableCell>
                <TableCell>{c.end_date}</TableCell>
                <TableCell>{c.num_reviews}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}

function ReviewsTracking() {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [cycleId, setCycleId] = useState('');
  const [cycles, setCycles] = useState([]);
  const [rows, setRows] = useState([]);
  const [folderPath, setFolderPath] = useState('');

  useEffect(()=>{ fetch('/api/projects').then(r=>r.ok?r.json():[]).then(setProjects).catch(()=>setProjects([])); },[]);
  useEffect(()=>{
    if (!projectId) { setCycles([]); setRows([]); return; }
    fetch(`/api/cycle_ids/${projectId}`).then(r=>r.ok?r.json():[]).then(list=>{ setCycles(list); setCycleId(list[0]||''); }).catch(()=>setCycles([]));
  }, [projectId]);
  useEffect(()=>{
    if (!projectId || !cycleId) { setRows([]); return; }
    fetch(`/api/review_tasks?project_id=${projectId}&cycle_id=${cycleId}`).then(r=>r.ok?r.json():[]).then(setRows).catch(()=>setRows([]));
  }, [projectId, cycleId]);

  const saveFolder = (reviewId) => {
    // Placeholder: send folderPath to backend for reviewId
    fetch(`/api/review_folder/${reviewId}`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ folder_path: folderPath })})
      .then(()=> alert('Folder saved'))
      .catch(()=>{});
  };

  return (
    <div>
      <h3>Reviews • Tracking</h3>
      <div style={{ display:'flex', gap:'1rem', alignItems:'center' }}>
        <FormControl size="small">
          <InputLabel>Project</InputLabel>
          <Select value={projectId} label="Project" onChange={e=>setProjectId(e.target.value)} style={{ minWidth: 240 }}>
            {projects.map(p=> <MenuItem key={p.project_id} value={p.project_id}>{p.project_name}</MenuItem>)}
          </Select>
        </FormControl>
        {!!cycles.length && (
          <FormControl size="small">
            <InputLabel>Cycle</InputLabel>
            <Select value={cycleId} label="Cycle" onChange={e=>setCycleId(e.target.value)}>
              {cycles.map(c=> <MenuItem key={c} value={c}>{c}</MenuItem>)}
            </Select>
          </FormControl>
        )}
        <TextField size="small" label="Review Folder" value={folderPath} onChange={e=>setFolderPath(e.target.value)} style={{ minWidth: 300 }} />
      </div>

      <TableContainer component={Paper} style={{ marginTop:'1rem' }}>
        <Table size="small">
          <TableHead><TableRow>
            <TableCell>Review ID</TableCell><TableCell>Service</TableCell><TableCell>Date</TableCell><TableCell>Status</TableCell><TableCell>Assignee</TableCell><TableCell>Actions</TableCell>
          </TableRow></TableHead>
          <TableBody>
            {rows.map(r=> (
              <TableRow key={r.schedule_id}>
                <TableCell>{r.schedule_id}</TableCell>
                <TableCell>{r.service_name || r.service || ''}</TableCell>
                <TableCell>{r.review_date || r.planned_start}</TableCell>
                <TableCell>{r.status || ''}</TableCell>
                <TableCell>{r.assignee || ''}</TableCell>
                <TableCell>
                  <Button size="small" onClick={()=>saveFolder(r.schedule_id)}>Save Folder</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}

function ReviewsServices() {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [services, setServices] = useState([]);

  useEffect(()=>{ fetch('/api/projects').then(r=>r.ok?r.json():[]).then(setProjects).catch(()=>setProjects([])); },[]);
  useEffect(()=>{
    if (!projectId) { setServices([]); return; }
    fetch(`/api/services/${projectId}`).then(r=>r.ok?r.json():[]).then(setServices).catch(()=>setServices([]));
  }, [projectId]);

  const addService = () => {
    const name = prompt('Service name'); if (!name) return;
    fetch('/api/services', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ project_id: projectId, service_name: name }) })
      .then(()=> fetch(`/api/services/${projectId}`).then(r=>r.json()).then(setServices));
  };

  return (
    <div>
      <h3>Reviews • Services</h3>
      <div style={{ display:'flex', gap:'1rem', alignItems:'center' }}>
        <FormControl size="small">
          <InputLabel>Project</InputLabel>
          <Select value={projectId} label="Project" onChange={e=>setProjectId(e.target.value)} style={{ minWidth: 240 }}>
            {projects.map(p=> <MenuItem key={p.project_id} value={p.project_id}>{p.project_name}</MenuItem>)}
          </Select>
        </FormControl>
        <Button size="small" variant="contained" onClick={addService}>Add Service</Button>
      </div>
      <TableContainer component={Paper} style={{ marginTop:'1rem' }}>
        <Table size="small">
          <TableHead><TableRow>
            <TableCell>Service</TableCell><TableCell>Description</TableCell>
          </TableRow></TableHead>
          <TableBody>
            {services.map(s=> (
              <TableRow key={s.service_id || s.id}>
                <TableCell>{s.service_name || s.name}</TableCell>
                <TableCell>{s.description || ''}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}

function ReviewsKanban() {
  const [columns, setColumns] = useState({
    todo: [{ id: 1, title: 'Define BEP' }],
    scheduled: [{ id: 2, title: 'Cycle 1 setup' }],
    inreview: [{ id: 3, title: 'Review #123' }],
    issued: [],
    actioned: [],
  });
  return (
    <div>
      <h3>Reviews • Kanban</h3>
      <div style={{ display:'flex', gap:'1rem' }}>
        {Object.entries(columns).map(([key, cards]) => (
          <div key={key} style={{ background:'#fafafa', border:'1px solid #ddd', padding:'0.5rem', width:220 }}>
            <h4 style={{ textTransform:'capitalize' }}>{key}</h4>
            {cards.map(c => <div key={c.id} style={{ background:'#fff', border:'1px solid #ccc', padding:'0.5rem', marginBottom:'0.5rem' }}>{c.title}</div>)}
          </div>
        ))}
      </div>
    </div>
  );
}

function ReviewsPage() {
  const [tab, setTab] = useState(0);
  return (
    <div>
      <Tabs value={tab} onChange={(e, v) => setTab(v)}>
        <Tab label="Planning" />
        <Tab label="Tracking" />
        <Tab label="Services" />
        <Tab label="Kanban" />
      </Tabs>
      <Box sx={{ p: 2 }}>
        {tab === 0 && <ReviewsPlanning />}
        {tab === 1 && <ReviewsTracking />}
        {tab === 2 && <ReviewsServices />}
        {tab === 3 && <ReviewsKanban />}
      </Box>
    </div>
  );
}

function ReviewTasks() {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [cycleId, setCycleId] = useState('');
  const [cycles, setCycles] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [projectDetails, setProjectDetails] = useState(null);
  const [reviewSummary, setReviewSummary] = useState(null);

  useEffect(() => {
    fetch('/api/projects')
      .then(res => res.json())
      .then(setProjects);
    fetch('/api/users')
      .then(res => res.json())
      .then(setUsers);
  }, []);

  useEffect(() => {
    if (projectId) {
      fetch(`/api/cycle_ids/${projectId}`)
        .then(res => res.json())
        .then(c => {
          setCycles(c);
          setCycleId(c[0] || '');
        });
      fetch(`/api/project/${projectId}`)
        .then(res => res.json())
        .then(setProjectDetails);
      const cid = cycleId || (cycles[0] || 1);
      fetch(`/api/review_summary?project_id=${projectId}&cycle_id=${cid}`)
        .then(res => res.json())
        .then(setReviewSummary);
      fetch(`/api/review_tasks?project_id=${projectId}&cycle_id=${cid}`)
        .then(res => res.json())
        .then(setTasks);
    } else {
      setProjectDetails(null);
      setReviewSummary(null);
      setTasks([]);
      setCycles([]);
      setCycleId('');
    }
  }, [projectId, cycleId]);

  const assignUser = (scheduleId, userId) => {
    fetch(`/api/review_task/${scheduleId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    }).then(() => {
      // refresh after update
      const cid = cycleId || (cycles[0] || 1);
      fetch(`/api/review_tasks?project_id=${projectId}&cycle_id=${cid}`)
        .then(res => res.json())
        .then(setTasks);
    });
  };

  return (
    <div>
      <h2>Review Tasks</h2>
      <select value={projectId} onChange={e => setProjectId(e.target.value)}>
        <option value="">Select Project</option>
        {projects.map(p => (
          <option key={p.project_id} value={p.project_id}>{p.project_name}</option>
        ))}
      </select>
      {cycles.length > 0 && (
        <select value={cycleId} onChange={e => setCycleId(e.target.value)} style={{marginLeft:'10px'}}>
          {cycles.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      )}
      {projectDetails && (
        <div style={{marginTop: '10px'}}>
          <h3>Project Details</h3>
          <p>Status: {projectDetails.status}</p>
          <p>Priority: {projectDetails.priority}</p>
          <p>Start: {projectDetails.start_date}</p>
          <p>End: {projectDetails.end_date}</p>
        </div>
      )}

      {reviewSummary && (
        <div style={{marginTop: '10px'}}>
          <h3>Review Summary</h3>
          <p>Cycle: {reviewSummary.cycle_id}</p>
          <p>Scoped: {reviewSummary.scoped_reviews}</p>
          <p>Completed: {reviewSummary.completed_reviews}</p>
        </div>
      )}

      <table border="1" cellPadding="4" style={{marginTop: '10px'}}>
        <thead>
          <tr>
            <th>Date</th>
            <th>Reviewer</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map(t => (
            <tr key={t.schedule_id}>
              <td>{t.review_date}</td>
              <td>
                <select value={t.user || ''} onChange={e => assignUser(t.schedule_id, e.target.value)}>
                  <option value="">--</option>
                  {users.map(u => (
                    <option key={u.user_id} value={u.user_id}>{u.name}</option>
                  ))}
                </select>
              </td>
              <td>{t.status || ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ReviewCycles() {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [cycles, setCycles] = useState([]);

  useEffect(() => {
    fetch('/api/projects')
      .then(res => res.json())
      .then(setProjects);
  }, []);

  useEffect(() => {
    if (projectId) {
      fetch(`/api/reviews/${projectId}`)
        .then(res => res.json())
        .then(setCycles);
    } else {
      setCycles([]);
    }
  }, [projectId]);

  return (
    <div>
      <h2>Review Cycles</h2>
      <select value={projectId} onChange={e => setProjectId(e.target.value)}>
        <option value="">Select Project</option>
        {projects.map(p => (
          <option key={p.project_id} value={p.project_id}>{p.project_name}</option>
        ))}
      </select>
      <table border="1" cellPadding="4" style={{marginTop:'10px'}}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Stage</th>
            <th>Start</th>
            <th>End</th>
            <th>Reviews</th>
          </tr>
        </thead>
        <tbody>
          {cycles.map(c => (
            <tr key={c.review_cycle_id}>
              <td>{c.review_cycle_id}</td>
              <td>{c.stage_id}</td>
              <td>{c.start_date}</td>
              <td>{c.end_date}</td>
              <td>{c.num_reviews}</td>
            </tr>
          ))}
        </tbody>
      </table>
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

  return (
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
  );
}


function App() {
  const [view, setView] = useState('reviews');
  return (
    <div>
      <div style={{ marginBottom:'1rem' }}>
        <Button size="small" variant={view==='reviews'?'contained':'outlined'} onClick={()=>setView('reviews')}>Reviews</Button>
        <Button size="small" variant={view==='projects'?'contained':'outlined'} onClick={()=>setView('projects')} style={{ marginLeft: 8 }}>Projects</Button>
      </div>
      {view === 'reviews' ? <ReviewsPage /> : <ProjectsView />}
    </div>
  );
}

ReactDOM.render(<App />, document.getElementById('root'));
