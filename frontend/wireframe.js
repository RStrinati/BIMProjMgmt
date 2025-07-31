const { useState } = React;
const { createClient } = supabase;

// TODO: replace with your Supabase project credentials
const supabaseUrl = 'https://your-project.supabase.co';
const supabaseKey = 'public-anon-key';
const supabaseClient = createClient(supabaseUrl, supabaseKey);

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

const pages = {
  projects: () => <Placeholder title="Projects" />,
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
