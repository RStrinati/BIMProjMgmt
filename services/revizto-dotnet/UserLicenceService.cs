using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Data.SqlClient;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Serilog;

namespace ReviztoDataExporter
{
    public class UserLicenceService
    {
        private readonly ReviztoApiClient _apiClient;
        private readonly string _outputDirectory;
        private readonly SQLServerHelper _dbHelper;
        private readonly string _connectionString;
        public UserLicenceService(ReviztoApiClient apiClient, string outputDirectory, string connectionString)
        {
            _apiClient = apiClient ?? throw new ArgumentNullException(nameof(apiClient));
            _outputDirectory = outputDirectory ?? throw new ArgumentNullException(nameof(outputDirectory));
            _dbHelper = SQLServerHelper.Instance;
            _connectionString = connectionString ?? throw new ArgumentNullException(nameof(connectionString));

          // ✅ Initialize the database connection
        _dbHelper.InitializeDatabase(_connectionString);
        }
        public async Task ExportIssuesForProject(Guid projectUuid)
        {
            try
            {
                Log.Information("Exporting issues for project {Uuid}", projectUuid);

                var allIssues = new List<IReadOnlyDictionary<string, object?>>();
                int page = 0;
                const int pageSize = 100;

                while (true)
                {
                    var issuesJson = await _apiClient.GetProjectIssues(projectUuid.ToString(), page, pageSize);
                    var issuesArray = issuesJson?["data"]?["data"] as JArray;

                    if (issuesArray == null || !issuesArray.Any()) break;

                    foreach (var issue in issuesArray)
                        allIssues.Add(ParseIssue(issue, projectUuid));

                    if (issuesArray.Count < pageSize)
                        break;


                    page++;
                }

                if (allIssues.Any())
                {
                    SaveIssuesToFile(projectUuid, allIssues);
                    _dbHelper.InsertReviztoProjectIssues(allIssues);
                    Log.Information("Exported {Count} issues for project {Uuid}", allIssues.Count, projectUuid);
                }
                else
                {
                    Log.Warning("No issues found for project {Uuid}", projectUuid);
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error exporting issues for project {Uuid}", projectUuid);
            }
        }

        public async Task FetchAndSaveUserLicensesAsync()
        {
            try
            {
                Log.Information("Starting user license, project, and issue retrieval...");
                var overallWatch = Stopwatch.StartNew();

                // 1. Fetch licenses
                var fetchLicWatch = Stopwatch.StartNew();
                var licensesJson = await _apiClient.GetUserLicenses();
                fetchLicWatch.Stop();
                Log.Information("Fetched licenses in {Duration}ms", fetchLicWatch.ElapsedMilliseconds);

                var licenseEntities = licensesJson? ["data"]? ["entities"] as JArray;
                if (licenseEntities == null || !licenseEntities.Any())
                {
                    Log.Warning("No licenses found in response.");
                    return;
                }
                var licenseCount = licensesJson? ["data"]? ["count"]?.ToObject<int>() ?? 0;
                Log.Information("User has {Count} licenses.", licenseCount);

                // 2. Filter to active admin licenses
                var adminLicenses = licenseEntities
                    .Where(l => l.Value<bool?>("frozen") == false && (l.Value<int?>("role") ?? 0) >= 4)
                    .ToList();
                Log.Information("Found {Count} admin-access licenses.", adminLicenses.Count);
                if (!adminLicenses.Any()) return;

                // 3. Save license metadata
                var licWatch = Stopwatch.StartNew();
                var licenseData = ProcessUserLicenses(new JArray(adminLicenses));
                SaveUserLicensesToDatabase(licenseData);
                SaveUserLicensesToFile(licenseData);
                licWatch.Stop();
                Log.Information("Processed and saved license metadata in {Duration}ms", licWatch.ElapsedMilliseconds);

                // 4. Fetch and parse all projects
                var allProjects = new List<IReadOnlyDictionary<string, object?>>();
                foreach (var lic in adminLicenses)
                {
                    var licUuid = lic.Value<string>("uuid");
                    if (string.IsNullOrWhiteSpace(licUuid))
                    {
                        Log.Warning("Skipping license with missing UUID.");
                        continue;
                    }
                    int page = 0;
                    const int pageSize = 100;
                    while (true)
                    {
                        try
                        {
                            var pageWatch = Stopwatch.StartNew();
                            var projResp = await _apiClient.GetProjectsForLicense(licUuid, page, pageSize);
                            pageWatch.Stop();
                            Log.Information("Fetched license {Uuid} projects page {Page} in {Duration}ms", licUuid, page, pageWatch.ElapsedMilliseconds);

                            var projArray = projResp? ["data"]? ["data"] as JArray;
                            if (projArray == null || !projArray.Any()) break;

                            foreach (var p in projArray)
                                allProjects.Add(ParseProject(p, licUuid));

                            if (projArray.Count < pageSize) break;
                            page++;
                        }
                        catch (Exception ex)
                        {
                            Log.Error(ex, "Failed to fetch projects for license {Uuid} page {Page}", licUuid, page);
                            break;
                        }
                    }
                }

                // 5. Deduplicate projects
                allProjects = allProjects
                    .GroupBy(p => p["projectUuid"]) 
                    .Select(g => g.First())
                    .ToList();

                SaveProjectsToFile(allProjects);

                _dbHelper.TruncateLicenseMembers();

                // 6. Fetch and save license members and project associations
                await FetchAndSaveLicenseMembersAsync(adminLicenses);


                // 7. Clear issues to avoid FK conflicts
                _dbHelper.TruncateReviztoProjectIssues();

                // 8. Insert projects
                var projDbWatch = Stopwatch.StartNew();
                _dbHelper.InsertReviztoProjects(allProjects);
                projDbWatch.Stop();
                Log.Information("Inserted {Count} projects in {Duration}ms", allProjects.Count, projDbWatch.ElapsedMilliseconds);

                // 9. Fetch and save issues per project (paged)
                foreach (var proj in allProjects)
                    {
                        var projectUuidStr = proj["projectUuid"]?.ToString();
                        if (!Guid.TryParse(projectUuidStr, out var projectUuid)) continue;

                        var projectId = _dbHelper.GetProjectIdByUuid(projectUuid);
                        if (projectId == -1)
                        {
                            Log.Warning("❌ Project ID for UUID {ProjectUuid} not found in database. Skipping comment fetch.", projectUuid);
                            continue;
                        }

                        var issues = _dbHelper.GetIssuesFromView(projectId); // ← You’ll need to implement this
                        foreach (var issue in issues)
                        {
                            var uuidStr = issue["uuid"]?.ToString();
                            if (Guid.TryParse(uuidStr, out var issueUuid))
                            {
                                await FetchAndInsertCommentsForIssue(issueUuid, projectId);
                            }
                        }
                    }

                
                overallWatch.Stop();
                Log.Information("All operations complete in {Duration}ms", overallWatch.ElapsedMilliseconds);
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error during FetchAndSaveUserLicensesAsync");
            }
            finally
            {
                Log.Information("FetchAndSaveUserLicensesAsync complete.");
            }
        }
        private async Task FetchAndSaveLicenseMembersAsync(List<JToken> adminLicenses)
        {
            foreach (var lic in adminLicenses)
            {
                var licUuid = lic.Value<string>("uuid");
                if (string.IsNullOrWhiteSpace(licUuid))
                {
                    Log.Warning("Skipping license with missing UUID.");
                    continue;
                }

                try
                {
                    Log.Information("Fetching members for license {Uuid}...", licUuid);
                    var membersJson = await _apiClient.GetLicenseTeamMembers(licUuid);
                    if (membersJson == null || membersJson["entities"] is not JArray entities)
                    {
                        Log.Warning("No members found for license {Uuid}", licUuid);
                        continue;
                    }

                    var members = new List<IReadOnlyDictionary<string, object?>>();

                    foreach (var m in entities.OfType<JObject>())
                    {
                        var user = m["user"] as JObject;
                        var memberUuid = m["uuid"]?.ToString(); // or user?["uuid"]

                        var dict = new Dictionary<string, object?>
                        {
                            ["uuid"] = memberUuid,
                            ["email"] = user?["email"]?.ToString(),
                            ["invitedAt"] = ParseNullableDateTime(m["invitedAt"]),
                            ["activated"] = m["activated"]?.ToObject<bool?>(),
                            ["deactivated"] = m["deactivated"]?.ToObject<bool?>(),
                            ["lastActive"] = ParseNullableDateTime(m["lastActive"]),
                            ["memberJson"] = m.ToString(Formatting.None)
                        };

                        members.Add(dict);
                    }

                    _dbHelper.InsertLicenseMembers(licUuid, members);
                }
                catch (Exception ex)
                {
                    Log.Error(ex, "Error fetching or inserting license members for license {Uuid}", licUuid);
                }
            }
        }
        
        // Add this at the end of your UserLicenceService class
        private static object ParseNullableDateTime(object? input)
        {
            if (input is string s && !string.IsNullOrWhiteSpace(s) && DateTime.TryParse(s, out var dt))
                return dt;

            return DBNull.Value;
        }

        // Helper: parse project into dictionary
        private IReadOnlyDictionary<string, object?> ParseProject(JToken proj, string licUuid)
        {
            return new Dictionary<string, object?>
            {
                ["projectId"] = proj.Value<int?>("id") ?? -1,
                ["projectUuid"] = Guid.TryParse(proj.Value<string>("uuid"), out var pg) ? pg : Guid.Empty,
                ["licenseUuid"] = Guid.TryParse(licUuid, out var lg) ? lg : Guid.Empty,
                ["title"] = proj.Value<string>("title"),
                ["created"] = DateTime.TryParse(proj.Value<string>("created"), out var c) ? (object)c : DBNull.Value,
                ["updated"] = DateTime.TryParse(proj.Value<string>("updated"), out var u) ? (object)u : DBNull.Value,
                ["projectJson"]   = proj.ToString(Formatting.None)
            };
        }
        
            
        private async Task FetchAndInsertCommentsForIssue(Guid issueUuid, int projectId)
        
        {
            int page = 0;
            var retrievalDate = new DateTime(2021, 01, 01); // Or set to DateTime.UtcNow.AddYears(-1)
            var collectedComments = new List<IReadOnlyDictionary<string, object?>>();

            Log.Information("Start fetching comments for issue {IssueUuid} in project {ProjectId} from {Date}", issueUuid, projectId, retrievalDate);

            while (true)
            {
                var json = await _apiClient.GetIssueComments(issueUuid.ToString(), projectId, retrievalDate, page);
                if (json == null)
                {
                    Log.Warning("Received null response when fetching comments for issue {IssueUuid} page {Page}", issueUuid, page);
                    break;
                }

                var commentsArray = json?["data"]?["data"] as JArray;

                Log.Information("Page {Page} for issue {IssueUuid} returned {Count} comments", page, issueUuid, commentsArray?.Count ?? 0);

                if (commentsArray == null || !commentsArray.Any()) break;

                collectedComments.Add(new Dictionary<string, object?>
                {
                    ["issueUuid"] = issueUuid,
                    ["projectId"] = projectId,
                    ["page"] = page,
                    ["retrievalDate"] = retrievalDate,
                    ["retrievedAt"] = DateTime.Now,
                    ["commentJson"] = commentsArray.ToString(Formatting.None)
                });

                int totalPages = json?["data"]?.Value<int>("pages") ?? 1;
                if (++page >= totalPages) break;
            }

            if (collectedComments.Any())
            {
                Log.Information("Inserting {Count} comments for issue {IssueUuid}", collectedComments.Count, issueUuid);
                _dbHelper.InsertIssueComments(collectedComments);
            }
            else
            {
                Log.Warning("No comments found for issue {IssueUuid}", issueUuid);
            }
        }


        // Helper: parse issue into dictionary
        private IReadOnlyDictionary<string, object?> ParseIssue(JToken issue, Guid projectUuid)
        {
            return new Dictionary<string, object?>
            {
                ["issueId"]    = issue.Value<int?>("id") ?? -1,
                ["projectUuid"]= projectUuid,
                ["title"]      = issue.SelectToken("title.value")?.ToString(),
                ["status"]     = issue.SelectToken("status.value")?.ToString(),
                ["assignee"]   = issue.SelectToken("assignee.value")?.ToString(),
                ["reporter"]   = issue.SelectToken("reporter.value")?.ToString(),
                ["created"]    = DateTime.TryParse(issue.SelectToken("created.value")?.ToString(), out var ic) ? (object)ic : DBNull.Value,
                ["issueJson"]  = issue.ToString(Formatting.None)
            };
        }

        // Helper: process licenses into list
        private List<IReadOnlyDictionary<string, object?>> ProcessUserLicenses(JArray arr)
        {
            return arr.Select(l => new Dictionary<string, object?>
            {
                ["uuid"]       = l.Value<string>("uuid"),
                ["name"]       = l.Value<string>("name"),
                ["expires"]    = DateTime.TryParse(l.Value<string>("expires"), out var ex) ? (object)ex : DBNull.Value,
                ["created"]    = DateTime.TryParse(l.Value<string>("created"), out var cr) ? (object)cr : DBNull.Value,
                ["region"]     = l.Value<string>("region"),
            }).ToList<IReadOnlyDictionary<string, object?>>();
        }

        // Helper: save licenses to DB
        private void SaveUserLicensesToDatabase(List<IReadOnlyDictionary<string, object?>> data)
        {
            _dbHelper.InsertUserLicenses(data);
        }

        // Helper: save licenses to file
        private void SaveUserLicensesToFile(List<IReadOnlyDictionary<string, object?>> data)
        {
            var path = Path.Combine(_outputDirectory, $"Licenses_{DateTime.Now:yyyyMMdd_HHmmss}.json");
            File.WriteAllText(path, JsonConvert.SerializeObject(data, Formatting.Indented));
        }

        // Helper: save projects to file
        private void SaveProjectsToFile(List<IReadOnlyDictionary<string, object?>> projects)
        {
            var path = Path.Combine(_outputDirectory, $"Projects_{DateTime.Now:yyyyMMdd_HHmmss}.json");
            File.WriteAllText(path, JsonConvert.SerializeObject(projects, Formatting.Indented));
        }

        // Helper: save issues to file
        private void SaveIssuesToFile(Guid projectUuid, List<IReadOnlyDictionary<string, object?>> issues)
        {
            var path = Path.Combine(_outputDirectory, $"Issues_{projectUuid}_{DateTime.Now:yyyyMMdd_HHmmss}.json");
            File.WriteAllText(path, JsonConvert.SerializeObject(issues, Formatting.Indented));
        }
    }
}
