const { useEffect, useState } = React;

function ReviewTasks() {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);

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
      fetch(`/api/review_tasks?project_id=${projectId}&cycle_id=1`)
        .then(res => res.json())
        .then(setTasks);
    }
  }, [projectId]);

  const assignUser = (scheduleId, userId) => {
    fetch(`/api/review_task/${scheduleId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    }).then(() => {
      // refresh after update
      fetch(`/api/review_tasks?project_id=${projectId}&cycle_id=1`)
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
