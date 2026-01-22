import { test, expect } from '@playwright/test';

const seedProject = {
  project_id: 1,
  project_name: 'Workspace Project',
  project_number: 'P-100',
  client_name: 'Mock Client',
  status: 'Active',
  internal_lead: 201,
  description: 'Mock project description',
};

const seedUsers = [
  { user_id: 201, name: 'Taylor Lead' },
  { user_id: 202, name: 'Alex Coordinator' },
];

const seedProjects = [
  seedProject,
  { project_id: 2, project_name: 'Other Project', project_number: 'P-200', client_name: 'Client B' },
];

const buildTask = (overrides: Record<string, any>) => ({
  task_id: overrides.task_id ?? 1,
  task_name: overrides.task_name ?? 'Kickoff',
  project_id: overrides.project_id ?? 1,
  task_date: overrides.task_date ?? '2024-02-01',
  assigned_to: overrides.assigned_to ?? 202,
  assigned_to_name: overrides.assigned_to_name ?? 'Alex Coordinator',
  notes: overrides.notes ?? '',
  task_items: overrides.task_items ?? [],
});

test.describe('Project workspace v2 tasks reuse', () => {
  test('create task in overview, see it in tasks tab and /tasks page', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('ff_project_workspace_v2', 'true');
    });

    const tasksByProject = new Map<number, any[]>([
      [1, [buildTask({ task_id: 1, task_name: 'Kickoff' })]],
      [2, [buildTask({ task_id: 2, project_id: 2, task_name: 'External review', assigned_to: null })]],
    ]);
    let nextTaskId = 100;

    await page.route('**/api/projects/1', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(seedProject),
      });
    });

    await page.route('**/api/projects', async (route) => {
      if (route.request().method() !== 'GET') {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(seedProjects),
      });
    });

    await page.route('**/api/users', async (route) => {
      if (route.request().method() !== 'GET') {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(seedUsers),
      });
    });

    await page.route('**/api/tasks/notes-view**', async (route) => {
      const url = new URL(route.request().url());
      const projectParam = url.searchParams.get('project_id');
      const limit = Number(url.searchParams.get('limit') ?? '25');
      const pageParam = Number(url.searchParams.get('page') ?? '1');

      const projectId = projectParam ? Number(projectParam) : null;
      const projectTasks = projectId ? tasksByProject.get(projectId) ?? [] : [];
      const allTasks = projectId
        ? projectTasks
        : Array.from(tasksByProject.values()).flat();

      const payloadTasks = allTasks.slice(0, limit);

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          tasks: payloadTasks,
          total: allTasks.length,
          page: pageParam,
          pageSize: limit,
        }),
      });
    });

    await page.route('**/api/tasks', async (route) => {
      if (route.request().method() !== 'POST') {
        await route.continue();
        return;
      }
      const payload = (await route.request().postDataJSON()) as Record<string, any>;
      const created = buildTask({
        task_id: nextTaskId,
        task_name: payload.task_name,
        project_id: payload.project_id,
        task_date: payload.task_date ?? '2024-02-02',
        assigned_to: payload.assigned_to ?? null,
        assigned_to_name: payload.assigned_to ? 'Alex Coordinator' : null,
      });
      nextTaskId += 1;
      const existing = tasksByProject.get(created.project_id) ?? [];
      tasksByProject.set(created.project_id, [created, ...existing]);

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(created),
      });
    });

    await page.goto('/projects/1');
    await expect(page.getByTestId('project-workspace-v2-overview')).toBeVisible();

    await page.getByPlaceholder('New task').fill('Review kickoff');
    await page.getByRole('button', { name: 'Add task' }).click();
    await expect(page.getByText('Created task "Review kickoff"')).toBeVisible();
    await expect(page.getByTestId('project-workspace-v2-recent-tasks')).toContainText('Review kickoff');

    await page.getByRole('tab', { name: 'Tasks' }).click();
    await expect(page.getByTestId('project-workspace-v2-tasks')).toBeVisible();
    await expect(page.getByText('Review kickoff')).toBeVisible();

    await page.goto('/tasks');
    await expect(page.getByRole('heading', { name: 'Tasks & Notes' })).toBeVisible();
    await expect(page.getByText('Review kickoff')).toBeVisible();
  });
});
