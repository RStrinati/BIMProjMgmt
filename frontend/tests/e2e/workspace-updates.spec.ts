import { test, expect } from '@playwright/test';

test.describe('Workspace Updates Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Mock project API
    await page.route(/.*\/api\/projects\/\d+$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            project_id: 7,
            project_name: 'Test Project',
            project_number: 'P-007',
            client_name: 'Test Client',
            status: 'Active',
            internal_lead: 101,
          }),
        });
        return;
      }
      await route.continue();
    });

    // Mock users API
    await page.route('**/api/users', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([{ user_id: 101, name: 'Test User' }]),
        });
        return;
      }
      await route.continue();
    });

    // Mock tasks API for Overview tab
    await page.route(/.*\/api\/tasks\?.*/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ tasks: [] }),
        });
        return;
      }
      await route.continue();
    });
  });

  test.describe('Overview Tab - Latest Update Only', () => {
    test('should show empty state when no updates exist', async ({ page }) => {
      // Mock empty updates list
      await page.route(/.*\/api\/projects\/\d+\/updates\?limit=1/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ updates: [], count: 0 }),
        });
      });

      await page.goto('http://localhost:5173/projects/7/workspace/overview');
      await page.waitForLoadState('networkidle');

      const latestUpdateCard = page.getByText('No updates yet. Post the first one above!');
      await expect(latestUpdateCard).toBeVisible();
    });

    test('should display the latest update', async ({ page }) => {
      // Mock latest update
      await page.route(/.*\/api\/projects\/\d+\/updates\?limit=1/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            updates: [
              {
                update_id: 1,
                project_id: 7,
                body: 'Completed structural review phase. Moving to MEP coordination next week.',
                created_by: 101,
                created_by_name: 'John Smith',
                created_at: '2024-01-18T14:30:00Z',
                updated_at: '2024-01-18T14:30:00Z',
                comment_count: 2,
              },
            ],
            count: 1,
          }),
        });
      });

      await page.goto('http://localhost:5173/projects/7/workspace/overview');
      await page.waitForLoadState('networkidle');

      const latestUpdateCard = page.getByTestId('latest-update-card');
      await expect(latestUpdateCard).toBeVisible();
      await expect(latestUpdateCard).toContainText('John Smith');
      await expect(latestUpdateCard).toContainText('Completed structural review phase');
      await expect(latestUpdateCard).toContainText('2 comments');
    });

    test('should post new update and refresh latest update', async ({ page }) => {
      // Mock empty updates initially
      let updatesList: any[] = [];

      await page.route(/.*\/api\/projects\/\d+\/updates\?limit=1/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ updates: updatesList, count: updatesList.length }),
        });
      });

      // Mock POST update
      await page.route(/.*\/api\/projects\/\d+\/updates$/, async (route) => {
        if (route.request().method() === 'POST') {
          const postData = route.request().postDataJSON();
          const newUpdate = {
            update_id: 1,
            project_id: 7,
            body: postData.body,
            created_by: 101,
            created_by_name: 'Test User',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            comment_count: 0,
          };
          updatesList = [newUpdate];

          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify(newUpdate),
          });
          return;
        }
        await route.continue();
      });

      await page.goto('http://localhost:5173/projects/7/workspace/overview');
      await page.waitForLoadState('networkidle');

      // Verify empty state
      await expect(page.getByText('No updates yet')).toBeVisible();

      // Type and post update
      const composer = page.getByTestId('workspace-update-composer').getByRole('textbox');
      await composer.fill('First project update!');

      const postButton = page.getByTestId('workspace-post-update-button');
      await postButton.click();

      // Wait for update to appear
      await page.waitForTimeout(500);

      // Verify latest update shows
      const latestUpdateCard = page.getByTestId('latest-update-card');
      await expect(latestUpdateCard).toBeVisible();
      await expect(latestUpdateCard).toContainText('First project update!');
    });

    test('should navigate to Updates tab when clicking View all updates', async ({ page }) => {
      await page.route(/.*\/api\/projects\/\d+\/updates/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ updates: [], count: 0 }),
        });
      });

      await page.goto('http://localhost:5173/projects/7/workspace/overview');
      await page.waitForLoadState('networkidle');

      const viewAllButton = page.getByText('View all updates →');
      await viewAllButton.click();

      await expect(page).toHaveURL(/\/projects\/7\/workspace\/updates/);
    });
  });

  test.describe('Updates Tab - History List', () => {
    test('should display updates list', async ({ page }) => {
      await page.route(/.*\/api\/projects\/\d+\/updates/, async (route) => {
        if (route.request().url().includes('limit=50')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              updates: [
                {
                  update_id: 3,
                  project_id: 7,
                  body: 'Final design review scheduled for next Tuesday.',
                  created_by: 101,
                  created_by_name: 'Jane Doe',
                  created_at: '2024-01-18T16:00:00Z',
                  comment_count: 1,
                },
                {
                  update_id: 2,
                  project_id: 7,
                  body: 'MEP coordination meeting completed. Resolved 5 clashes.',
                  created_by: 102,
                  created_by_name: 'Bob Wilson',
                  created_at: '2024-01-17T10:30:00Z',
                  comment_count: 3,
                },
                {
                  update_id: 1,
                  project_id: 7,
                  body: 'Completed structural review phase. Moving to MEP coordination next week.',
                  created_by: 101,
                  created_by_name: 'John Smith',
                  created_at: '2024-01-15T14:30:00Z',
                  comment_count: 2,
                },
              ],
              count: 3,
            }),
          });
          return;
        }
        await route.continue();
      });

      await page.goto('http://localhost:5173/projects/7/workspace/updates');
      await page.waitForLoadState('networkidle');

      const updatesList = page.getByTestId('updates-list');
      await expect(updatesList).toBeVisible();

      // Verify all updates are displayed (newest first)
      const update1 = page.getByTestId('update-row-3');
      await expect(update1).toBeVisible();
      await expect(update1).toContainText('Final design review scheduled');
      await expect(update1).toContainText('1 comment');

      const update2 = page.getByTestId('update-row-2');
      await expect(update2).toBeVisible();
      await expect(update2).toContainText('MEP coordination meeting completed');
      await expect(update2).toContainText('3 comments');

      const update3 = page.getByTestId('update-row-1');
      await expect(update3).toBeVisible();
      await expect(update3).toContainText('Completed structural review phase');
      await expect(update3).toContainText('2 comments');
    });

    test('should select update and display in right panel', async ({ page }) => {
      await page.route(/.*\/api\/projects\/\d+\/updates/, async (route) => {
        if (route.request().url().includes('limit=50')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              updates: [
                {
                  update_id: 1,
                  project_id: 7,
                  body: 'Completed structural review phase.',
                  created_by: 101,
                  created_by_name: 'John Smith',
                  created_at: '2024-01-15T14:30:00Z',
                  comment_count: 2,
                },
              ],
              count: 1,
            }),
          });
          return;
        }
        await route.continue();
      });

      // Mock single update detail
      await page.route(/.*\/api\/updates\/1$/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            update_id: 1,
            project_id: 7,
            body: 'Completed structural review phase. All models validated.',
            created_by: 101,
            created_by_name: 'John Smith',
            created_at: '2024-01-15T14:30:00Z',
            updated_at: '2024-01-15T14:30:00Z',
          }),
        });
      });

      // Mock comments
      await page.route(/.*\/api\/updates\/1\/comments/, async (route) => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              comments: [
                {
                  comment_id: 1,
                  update_id: 1,
                  body: 'Great work on the structural review!',
                  created_by: 102,
                  created_by_name: 'Jane Doe',
                  created_at: '2024-01-15T15:00:00Z',
                },
                {
                  comment_id: 2,
                  update_id: 1,
                  body: 'When do we start MEP coordination?',
                  created_by: 103,
                  created_by_name: 'Bob Wilson',
                  created_at: '2024-01-15T16:30:00Z',
                },
              ],
              count: 2,
            }),
          });
          return;
        }
        await route.continue();
      });

      await page.goto('http://localhost:5173/projects/7/workspace/updates');
      await page.waitForLoadState('networkidle');

      // Click on update
      const updateRow = page.getByTestId('update-row-1');
      await updateRow.click();
      await page.waitForTimeout(200);

      // Verify URL updated
      // Selection uses unencoded colon in URL (e.g., ?sel=update:1)
      await expect(page).toHaveURL(/.*\?sel=update:1/);

      // Verify right panel shows update detail
      const updateDetailPanel = page.getByTestId('update-detail-panel');
      await expect(updateDetailPanel).toBeVisible();
      await expect(updateDetailPanel).toContainText('Completed structural review phase');
      await expect(updateDetailPanel).toContainText('Comments (2)');
      await expect(updateDetailPanel).toContainText('Great work on the structural review!');
      await expect(updateDetailPanel).toContainText('When do we start MEP coordination?');
    });

    test('should highlight selected update', async ({ page }) => {
      await page.route(/.*\/api\/projects\/\d+\/updates/, async (route) => {
        if (route.request().url().includes('limit=50')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              updates: [
                { update_id: 2, project_id: 7, body: 'Update 2', created_by_name: 'User', created_at: '2024-01-18T10:00:00Z', comment_count: 0 },
                { update_id: 1, project_id: 7, body: 'Update 1', created_by_name: 'User', created_at: '2024-01-17T10:00:00Z', comment_count: 0 },
              ],
              count: 2,
            }),
          });
          return;
        }
        await route.continue();
      });

      await page.route(/.*\/api\/updates\/\d+$/, async (route) => {
        const updateId = route.request().url().match(/updates\/(\d+)/)?.[1];
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            update_id: parseInt(updateId || '1'),
            project_id: 7,
            body: `Update ${updateId}`,
            created_by_name: 'User',
            created_at: '2024-01-17T10:00:00Z',
          }),
        });
      });

      await page.route(/.*\/api\/updates\/\d+\/comments/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ comments: [], count: 0 }),
        });
      });

      await page.goto('http://localhost:5173/projects/7/workspace/updates');
      await page.waitForLoadState('networkidle');

      // Click first update
      const update1 = page.getByTestId('update-row-2');
      await update1.click();
      await page.waitForTimeout(200);

      // Verify first update has selected background
      await expect(update1).toHaveCSS('background-color', /rgba?\(.*\)/); // action.selected color

      // Click second update
      const update2 = page.getByTestId('update-row-1');
      await update2.click();
      await page.waitForTimeout(200);

      // Verify second update is now selected
      await expect(update2).toHaveCSS('background-color', /rgba?\(.*\)/);
    });

    test('should add comment to update', async ({ page }) => {
      let commentsList: any[] = [];

      await page.route(/.*\/api\/projects\/\d+\/updates/, async (route) => {
        if (route.request().url().includes('limit=50')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              updates: [
                { update_id: 1, project_id: 7, body: 'Test update', created_by_name: 'User', created_at: '2024-01-17T10:00:00Z', comment_count: commentsList.length },
              ],
              count: 1,
            }),
          });
          return;
        }
        await route.continue();
      });

      await page.route(/.*\/api\/updates\/1$/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            update_id: 1,
            project_id: 7,
            body: 'Test update',
            created_by_name: 'User',
            created_at: '2024-01-17T10:00:00Z',
          }),
        });
      });

      await page.route(/.*\/api\/updates\/1\/comments/, async (route) => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ comments: commentsList, count: commentsList.length }),
          });
          return;
        }

        if (route.request().method() === 'POST') {
          const postData = route.request().postDataJSON();
          const newComment = {
            comment_id: commentsList.length + 1,
            update_id: 1,
            body: postData.body,
            created_by: 101,
            created_by_name: 'Test User',
            created_at: new Date().toISOString(),
          };
          commentsList.push(newComment);

          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify(newComment),
          });
          return;
        }
        await route.continue();
      });

      await page.goto('http://localhost:5173/projects/7/workspace/updates');
      await page.waitForLoadState('networkidle');

      // Select update
      await page.getByTestId('update-row-1').click();
      await page.waitForTimeout(200);

      // Verify no comments initially
      const updateDetailPanel = page.getByTestId('update-detail-panel');
      await expect(updateDetailPanel).toContainText('Comments (0)');

      // Add comment
      const commentComposer = page.getByTestId('update-comment-composer').getByRole('textbox');
      await commentComposer.fill('This is a test comment!');

      const addCommentButton = page.getByTestId('update-add-comment-button');
      await addCommentButton.click();

      // Wait for comment to appear
      await page.waitForTimeout(500);

      // Verify comment appears
      await expect(updateDetailPanel).toContainText('Comments (1)');
      await expect(updateDetailPanel).toContainText('This is a test comment!');
    });

    test('should clear selection when Escape is pressed', async ({ page }) => {
      await page.route(/.*\/api\/projects\/\d+\/updates/, async (route) => {
        if (route.request().url().includes('limit=50')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              updates: [
                { update_id: 1, project_id: 7, body: 'Test update', created_by_name: 'User', created_at: '2024-01-17T10:00:00Z', comment_count: 0 },
              ],
              count: 1,
            }),
          });
          return;
        }
        await route.continue();
      });

      await page.route(/.*\/api\/updates\/1/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            update_id: 1,
            project_id: 7,
            body: 'Test update',
            created_by_name: 'User',
            created_at: '2024-01-17T10:00:00Z',
          }),
        });
      });

      await page.route(/.*\/api\/updates\/1\/comments/, async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ comments: [], count: 0 }),
        });
      });

      await page.goto('http://localhost:5173/projects/7/workspace/updates');
      await page.waitForLoadState('networkidle');

      // Select update
      await page.getByTestId('update-row-1').click();
      await page.waitForTimeout(200);

      // Verify update detail panel is visible
      const updateDetailPanel = page.getByTestId('update-detail-panel');
      await expect(updateDetailPanel).toBeVisible();

      // Press Escape
      await page.keyboard.press('Escape');
      await page.waitForTimeout(200);

      // Verify URL selection is cleared
      await expect(page).toHaveURL(/^(?!.*\?sel=)/);

      // Verify update detail panel is no longer visible
      await expect(updateDetailPanel).not.toBeVisible();

      // Verify summary panel is shown
      const rightPanel = page.getByTestId('workspace-right-panel');
      await expect(rightPanel).toContainText('Updates Summary');
    });
  });
});
