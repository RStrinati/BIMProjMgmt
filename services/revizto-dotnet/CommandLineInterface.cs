using System;
using System.Collections.Generic;
using System.Data.SqlClient;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Serilog;

namespace ReviztoDataExporter
{
    public class ProjectInfo
    {
        public string ProjectId { get; set; } = "";
        public string ProjectName { get; set; } = "";
        public string LicenseId { get; set; } = "";
        public DateTime? LastModified { get; set; }
    }

    public class CommandLineInterface
    {
        private readonly UserLicenceService _userLicenceService;
        private readonly string _connectionString;
        private readonly ILogger _logger;

        public CommandLineInterface(UserLicenceService userLicenceService, string connectionString, ILogger logger)
        {
            _userLicenceService = userLicenceService;
            _connectionString = connectionString;
            _logger = logger;
        }

        public async Task<int> ExecuteAsync(string[] args)
        {
            try
            {
                if (args.Length == 0)
                {
                    ShowHelp();
                    return 0;
                }

                var command = args[0].ToLower();
                
                switch (command)
                {
                    case "refresh":
                        return await RefreshProjectsAsync();
                    
                    case "export":
                        if (args.Length < 2)
                        {
                            Console.WriteLine("Error: Project ID required for export command");
                            return 1;
                        }
                        return await ExportProjectAsync(args[1], args.Length > 2 ? args[2] : "");
                    
                    case "list-projects":
                        return await ListProjectsAsync();
                    
                    case "export-all":
                        return await ExportAllProjectsAsync(args.Length > 1 ? args[1] : "");
                    
                    case "status":
                        return await GetStatusAsync();
                    
                    default:
                        Console.WriteLine($"Unknown command: {command}");
                        ShowHelp();
                        return 1;
                }
            }
            catch (Exception ex)
            {
                _logger.Error(ex, "Command execution failed");
                Console.WriteLine($"Error: {ex.Message}");
                return 1;
            }
        }

        private async Task<int> RefreshProjectsAsync()
        {
            Console.WriteLine("Refreshing projects from Revizto API...");
            await _userLicenceService.FetchAndSaveUserLicensesAsync();
            
            var projects = GetProjects();
            var result = new
            {
                success = true,
                message = "Projects refreshed successfully",
                projectCount = projects.Count,
                timestamp = DateTime.Now
            };
            
            Console.WriteLine(JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }

        private async Task<int> ExportProjectAsync(string projectId, string outputPath)
        {
            if (!Guid.TryParse(projectId, out var guid))
            {
                Console.WriteLine($"Error: Invalid project ID format: {projectId}");
                return 1;
            }

            Console.WriteLine($"Exporting project {projectId}...");
            
            try
            {
                var exportedFile = await ExportProjectIssuesAsync(guid, outputPath);
                var result = new
                {
                    success = true,
                    message = "Project exported successfully",
                    projectId = projectId,
                    exportedFile = exportedFile,
                    timestamp = DateTime.Now
                };
                
                Console.WriteLine(JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                var result = new
                {
                    success = false,
                    message = ex.Message,
                    projectId = projectId,
                    timestamp = DateTime.Now
                };
                
                Console.WriteLine(JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }

        private async Task<int> ListProjectsAsync()
        {
            var projects = GetProjects();
            var result = new
            {
                success = true,
                projects = projects.Select(p => new
                {
                    id = p.ProjectId,
                    name = p.ProjectName,
                    licenseId = p.LicenseId,
                    lastModified = p.LastModified
                }).ToList(),
                count = projects.Count,
                timestamp = DateTime.Now
            };
            
            Console.WriteLine(JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }

        private async Task<int> ExportAllProjectsAsync(string outputDir)
        {
            var projects = GetProjects();
            var results = new List<object>();
            
            Console.WriteLine($"Exporting {projects.Count} projects...");
            
            foreach (var project in projects)
            {
                try
                {
                    var exportedFile = await ExportProjectIssuesAsync(Guid.Parse(project.ProjectId), outputDir);
                    results.Add(new
                    {
                        projectId = project.ProjectId,
                        projectName = project.ProjectName,
                        success = true,
                        exportedFile = exportedFile
                    });
                }
                catch (Exception ex)
                {
                    results.Add(new
                    {
                        projectId = project.ProjectId,
                        projectName = project.ProjectName,
                        success = false,
                        error = ex.Message
                    });
                }
            }
            
            var result = new
            {
                success = true,
                message = "Bulk export completed",
                results = results,
                totalProjects = projects.Count,
                successfulExports = results.Count(r => (bool)r.GetType().GetProperty("success")!.GetValue(r)!),
                timestamp = DateTime.Now
            };
            
            Console.WriteLine(JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }

        private async Task<int> GetStatusAsync()
        {
            var projects = GetProjects();
            
            var result = new
            {
                success = true,
                status = new
                {
                    projectCount = projects.Count,
                    databaseConnected = !string.IsNullOrEmpty(_connectionString),
                    lastRefresh = projects.Any() ? projects.Max(p => p.LastModified) : (DateTime?)null
                },
                projects = projects.Take(5).Select(p => new
                {
                    id = p.ProjectId,
                    name = p.ProjectName,
                    lastModified = p.LastModified
                }).ToList(),
                timestamp = DateTime.Now
            };
            
            Console.WriteLine(JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }

        private List<ProjectInfo> GetProjects()
        {
            var projects = new List<ProjectInfo>();
            
            using var conn = new SqlConnection(_connectionString);
            conn.Open();
            using var cmd = new SqlCommand("SELECT projectUuid, title, licenseUuid FROM tblReviztoProjects ORDER BY title", conn);
            using var reader = cmd.ExecuteReader();
            
            while (reader.Read())
            {
                projects.Add(new ProjectInfo
                {
                    ProjectId = reader["projectUuid"].ToString() ?? "",
                    ProjectName = reader["title"].ToString() ?? "",
                    LicenseId = reader["licenseUuid"].ToString() ?? "",
                    LastModified = DateTime.Now
                });
            }
            
            return projects;
        }

        private async Task<string> ExportProjectIssuesAsync(Guid projectId, string outputPath)
        {
            var exportDir = string.IsNullOrEmpty(outputPath) ? "Exports" : outputPath;
            if (!Directory.Exists(exportDir))
            {
                Directory.CreateDirectory(exportDir);
            }

            var timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
            var filename = $"Issues_{projectId}_{timestamp}.json";
            var fullPath = Path.Combine(exportDir, filename);

            var issues = new List<Dictionary<string, object>>();
            using var conn = new SqlConnection(_connectionString);
            conn.Open();
            using var cmd = new SqlCommand($"SELECT * FROM vReviztoProjectIssues WHERE projectId = '{projectId}'", conn);
            using var reader = cmd.ExecuteReader();
            
            while (reader.Read())
            {
                var issue = new Dictionary<string, object>();
                for (int i = 0; i < reader.FieldCount; i++)
                {
                    issue[reader.GetName(i)] = reader.GetValue(i);
                }
                issues.Add(issue);
            }
            
            var jsonString = JsonSerializer.Serialize(issues, new JsonSerializerOptions { WriteIndented = true });
            await File.WriteAllTextAsync(fullPath, jsonString);
            
            return fullPath;
        }

        private void ShowHelp()
        {
            Console.WriteLine(@"
Revizto Data Exporter - Command Line Interface

Usage: ReviztoDataExporter.exe <command> [options]

Commands:
  refresh                     - Refresh projects from Revizto API
  list-projects              - List all available projects (JSON format)  
  export <project-id> [path] - Export specific project issues
  export-all [output-dir]    - Export all projects
  status                     - Show application status and summary

Examples:
  ReviztoDataExporter.exe refresh
  ReviztoDataExporter.exe list-projects
  ReviztoDataExporter.exe export 429b27f4-4359-40d6-a526-c2ac8374a3c9
  ReviztoDataExporter.exe export 429b27f4-4359-40d6-a526-c2ac8374a3c9 C:\Exports
  ReviztoDataExporter.exe export-all
  ReviztoDataExporter.exe status

All commands return JSON output for easy parsing in Python applications.
Exit codes: 0 = Success, 1 = Error
");
        }
    }
}