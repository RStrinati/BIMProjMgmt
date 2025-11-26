using System;
using System.Collections.Generic;
using System.Data.SqlClient;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;
using ReviztoDataExporter;

public partial class ExportForm : Form
{
    private readonly UserLicenceService _exportService;
    private readonly string _connectionString;

    public ExportForm(UserLicenceService exportService, string connectionString)
    {
        _exportService = exportService;
        _connectionString = connectionString;

        InitializeForm();  // ✅ This already sets up your form manually
    }

    private CheckedListBox? projectList;
    private Button? exportButton;
    private Label? statusLabel;

    private void InitializeForm()
    {
        this.Text = "Revizto Project Exporter";
        this.Width = 500;
        this.Height = 400;

        var refreshButton = new Button
        {
            Text = "Refresh Projects",
            Dock = DockStyle.Top,
            Height = 40
        };
        refreshButton.Click += async (s, e) =>
        {
            await RefreshProjectsFromApi();
        };

        projectList = new CheckedListBox
        {
            Dock = DockStyle.Top,
            Height = 250
        };

        exportButton = new Button
        {
            Text = "Export Issues",
            Dock = DockStyle.Top,
            Height = 40
        };
        exportButton.Click += ExportButton_Click;

        statusLabel = new Label
        {
            Text = "Select projects and click Export.",
            Dock = DockStyle.Top,
            Height = 40
        };

        this.Controls.Add(statusLabel);
        this.Controls.Add(exportButton);
        this.Controls.Add(projectList);
        this.Controls.Add(refreshButton);
        LoadProjects();
    }

    private void LoadProjects()
    {
        var items = new List<ProjectItem>();

        using var conn = new SqlConnection(_connectionString);
        conn.Open();
        using var cmd = new SqlCommand("SELECT projectUuid, title FROM tblReviztoProjects ORDER BY title;", conn);
        using var reader = cmd.ExecuteReader();
        while (reader.Read())
        {
            items.Add(new ProjectItem
            {
                Title = reader.GetString(1),
                ProjectUuid = reader.GetGuid(0)
            });
        }

        foreach (var item in items)
        {
            if (projectList != null)
            {
                projectList.Items.Add(item);
            }
        }
    }

    private async Task RefreshProjectsFromApi()
    {
        try
        {
            if (statusLabel != null)
                statusLabel.Text = "Refreshing projects from API...";

            // Clear existing project list
            if (projectList != null)
            {
                projectList.Items.Clear();
            }

            // Fetch fresh data from API
            await _exportService.FetchAndSaveUserLicensesAsync();

            // Reload projects from updated database
            LoadProjects();

            if (statusLabel != null)
                statusLabel.Text = "Projects refreshed successfully.";
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Error refreshing projects:\n{ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            if (statusLabel != null)
                statusLabel.Text = "Error refreshing projects.";
        }
    }

    private async void ExportButton_Click(object? sender, EventArgs? e)
    {
        var selectedItems = projectList != null
            ? projectList.CheckedItems.Cast<ProjectItem>().ToList()
            : new List<ProjectItem>();
        if (!selectedItems.Any())
        {
            MessageBox.Show("Please select at least one project.");
            return;
        }

        if (exportButton != null)
            exportButton.Enabled = false;
        if (statusLabel != null)
            statusLabel.Text = "Exporting issues...";

        try
        {
            foreach (var item in selectedItems)
            {
                await _exportService.ExportIssuesForProject(item.ProjectUuid);
            }

            MessageBox.Show("Export completed successfully.");
        }
        catch (Exception ex)
        {
            MessageBox.Show($"An error occurred during export:\n{ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        finally
        {
            if (exportButton != null)
                exportButton.Enabled = true;
            if (statusLabel != null)
                statusLabel.Text = "Export complete.";
        }
    }
}

public class ProjectItem
{
    public Guid ProjectUuid { get; set; }
    public string? Title { get; set; }

    public override string ToString() => Title ?? string.Empty;
}