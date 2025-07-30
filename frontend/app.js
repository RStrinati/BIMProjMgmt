const { useEffect, useState } = React;

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

ReactDOM.render(<ReviewTasks />, document.getElementById('root'));
