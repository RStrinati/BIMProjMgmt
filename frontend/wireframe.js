const { useState, useEffect } = React;

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

function ProjectsPage() {
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    fetch('/api/projects')
      .then(res => res.json())
      .then(setProjects);
  }, []);

  const addProject = () => {
    const name = prompt('Project name');
    if (!name) return;
    fetch('/api/project', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_name: name })
    }).then(() => {
      fetch('/api/projects')
        .then(res => res.json())
        .then(setProjects);
    });
  };

  return (
    <div>
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <h3>Projects</h3>
        <button onClick={addProject}>+ New Project</button>
      </div>
      <table className="project-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
          </tr>
        </thead>
        <tbody>
          {projects.map(p => (
            <tr key={p.project_id}>
              <td>{p.project_id}</td>
              <td>{p.project_name}</td>
            </tr>
          ))}
        </tbody>
      </table>
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
