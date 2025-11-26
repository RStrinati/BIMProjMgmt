using System;
using System.Collections.Generic;
using System.Data.SqlClient;
using Serilog;
using Newtonsoft.Json;

namespace ReviztoDataExporter
{
    public static class DictionaryExtensions
    {
        public static object? GetValue(this IReadOnlyDictionary<string, object?> dict, string key)
            => dict.TryGetValue(key, out var value) ? value : null;
    }

    public sealed class SQLServerHelper
    {
        private static readonly Lazy<SQLServerHelper> lazy = new(() => new SQLServerHelper());
        public static SQLServerHelper Instance => lazy.Value;

        private string? _connectionString;
        private SQLServerHelper() { }

        public void InitializeDatabase(string connectionString)
        {
            _connectionString = connectionString ?? throw new ArgumentNullException(nameof(connectionString));
            Log.Information("Database initialized.");
        }

        public void TruncateUserLicenses()
            => ExecuteWithConnection(conn =>
            {
                using var cmd = new SqlCommand("TRUNCATE TABLE tblUserLicenses;", conn);
                cmd.ExecuteNonQuery();
                Log.Information("tblUserLicenses truncated.");
            });

        public void InsertUserLicenses(List<IReadOnlyDictionary<string, object?>> licenses)
        {
            if (licenses == null || licenses.Count == 0)
            {
                Log.Warning("No license data to insert.");
                return;
            }

            ExecuteWithConnection(conn =>
            {
                TruncateUserLicenses();
                const string query = @"INSERT INTO tblUserLicenses (
                    uuid, name, expires, created, region, ownerId, ownerUuid, ownerEmail,
                    planUsers, planProjects, slotsProjects, slotsUsers,
                    clashAutomation, allowBeExternalGuest, allowGuestsHere, allowBCFExport, allowApiAccess
                ) VALUES (
                    @uuid, @name, @expires, @created, @region, @ownerId, @ownerUuid, @ownerEmail,
                    @planUsers, @planProjects, @slotsProjects, @slotsUsers,
                    @clashAutomation, @allowBeExternalGuest, @allowGuestsHere, @allowBCFExport, @allowApiAccess
                );";
                int totalInserted = 0;
                foreach (var lic in licenses)
                {
                    var uuidStr = lic.GetValue("uuid")?.ToString();
                    if (!Guid.TryParse(uuidStr, out var uuid))
                    {
                        Log.Warning($"Invalid or missing UUID '{uuidStr}', skipping record.");
                        continue;
                    }

                    using var cmd = new SqlCommand(query, conn);
                    cmd.Parameters.AddWithValue("@uuid", uuid);
                    cmd.Parameters.AddWithValue("@name", lic.GetValue("name") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@expires", lic.GetValue("expires") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@created", lic.GetValue("created") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@region", lic.GetValue("region") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@ownerId", lic.GetValue("ownerId") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@ownerUuid", lic.GetValue("ownerUuid") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@ownerEmail", lic.GetValue("ownerEmail") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@planUsers", lic.GetValue("planUsers") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@planProjects", lic.GetValue("planProjects") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@slotsProjects", lic.GetValue("slotsProjects") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@slotsUsers", lic.GetValue("slotsUsers") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@clashAutomation", lic.GetValue("clashAutomation") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@allowBeExternalGuest", lic.GetValue("allowBeExternalGuest") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@allowGuestsHere", lic.GetValue("allowGuestsHere") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@allowBCFExport", lic.GetValue("allowBCFExport") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@allowApiAccess", lic.GetValue("allowApiAccess") ?? DBNull.Value);
                    cmd.ExecuteNonQuery();
                    totalInserted++;
                }

                Log.Information($"Inserted {licenses.Count} license records.");
            });
        }

        public void TruncateLicenseMembers()
            => ExecuteWithConnection(conn =>
            {
                using var cmd = new SqlCommand("TRUNCATE TABLE tblLicenseMembers;", conn);
                cmd.ExecuteNonQuery();
                Log.Information("tblLicenseMembers truncated.");
            });

        public void InsertLicenseMembers(string licenseUuid, List<IReadOnlyDictionary<string, object?>> members)
        {
            if (members == null || members.Count == 0)
            {
                Log.Warning($"No members to insert for license {licenseUuid}.");
                return;
            }

            ExecuteWithConnection(conn =>
            {
                const string deleteQuery = "DELETE FROM tblLicenseMembers WHERE licenseUuid = @licenseUuid";
                if (!Guid.TryParse(licenseUuid, out var licUuid))
                {
                    Log.Warning($"Invalid licenseUuid '{licenseUuid}', skipping members.");
                    return;
                }

                using var deleteCmd = new SqlCommand(deleteQuery, conn);
                deleteCmd.Parameters.AddWithValue("@licenseUuid", licUuid);
                var deleted = deleteCmd.ExecuteNonQuery();
                Log.Information($"Deleted {deleted} existing members for license {licenseUuid}.");

                const string insertQuery = @"INSERT INTO tblLicenseMembers (
                    licenseUuid, memberUuid, email, invitedAt, activated, deactivated, lastActive, memberJson
                ) VALUES (
                    @licenseUuid, @memberUuid, @email, @invitedAt, @activated, @deactivated, @lastActive, @memberJson
                );";

                int totalInserted = 0;
                foreach (var m in members)
                {
                    var memStr = m.GetValue("uuid")?.ToString();  // key is "uuid"
                    if (!Guid.TryParse(memStr, out var memUuid))
                    {
                        Log.Warning($"Invalid uuid '{memStr}', skipping.");
                        continue;
                    }

                    using var cmd = new SqlCommand(insertQuery, conn);
                    cmd.Parameters.AddWithValue("@licenseUuid", licUuid);
                    cmd.Parameters.AddWithValue("@memberUuid", memUuid);
                    cmd.Parameters.AddWithValue("@email", m.GetValue("email") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@invitedAt", m.GetValue("invitedAt") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@activated", m.GetValue("activated") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@deactivated", m.GetValue("deactivated") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@lastActive", m.GetValue("lastActive") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@memberJson", JsonConvert.SerializeObject(m));



                    cmd.ExecuteNonQuery();
                    totalInserted++;
                }

                Log.Information($"Inserted {members.Count} members for license {licenseUuid}.");
            });
        }

        public void InsertReviztoProjects(List<IReadOnlyDictionary<string, object?>> projects)
        {
            if (projects == null || projects.Count == 0)
                return;

            using var conn = new SqlConnection(_connectionString);
            conn.Open();
            using var transaction = conn.BeginTransaction();

            try
            {
                // Delete existing projects per license
                var licenseUuids = projects
                    .Select(p => p["licenseUuid"])
                    .Where(v => v is Guid)
                    .Cast<Guid>()
                    .Distinct()
                    .ToList();

                foreach (var lic in licenseUuids)
                {
                    using var del = new SqlCommand("DELETE FROM tblReviztoProjects WHERE licenseUuid = @licUuid", conn, transaction);
                    del.Parameters.AddWithValue("@licUuid", lic);
                    var d = del.ExecuteNonQuery();
                    Log.Information($"Deleted {d} existing projects for license {lic}.");
                }

                const string ins = @"INSERT INTO tblReviztoProjects (
                    projectId, licenseUuid, projectUuid, title,
                    created, updated, region, archived, frozen, ownerEmail, projectJson
                ) VALUES (
                    @projectId, @licUuid, @projUuid, @title,
                    @created, @updated, @region, @archived, @frozen, @ownerEmail, @projectJson
                );";
                int totalInserted = 0;
                foreach (var p in projects)
                {
                    using var cmd = new SqlCommand(ins, conn, transaction);
                    cmd.Parameters.AddWithValue("@projectId", p.GetValue("projectId") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@licUuid", p.GetValue("licenseUuid") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@projUuid", p.GetValue("projectUuid") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@title", p.GetValue("title") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@created", p.GetValue("created") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@updated", p.GetValue("updated") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@region", p.GetValue("region") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@archived", p.GetValue("archived") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@frozen", p.GetValue("frozen") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@ownerEmail", p.GetValue("ownerEmail") ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@projectJson", p.GetValue("projectJson") ?? DBNull.Value);
                    cmd.ExecuteNonQuery();
                    totalInserted++;
                }

                transaction.Commit();
                Log.Information($"Inserted {projects.Count} Revizto project records into database.");
            }
            catch (Exception ex)
            {
                transaction.Rollback();
                Log.Error(ex, "Error inserting Revizto projects.");
                throw;
            }
        }
    public void InsertIssueComments(List<IReadOnlyDictionary<string, object?>> comments)
    {
        if (comments == null || comments.Count == 0)
            return;

        using var conn = new SqlConnection(_connectionString);
        conn.Open();
        using var transaction = conn.BeginTransaction();

        try
        {
            const string ins = @"INSERT INTO tblReviztoIssueComments (
                issueUuid, projectId, page, retrievalDate, retrievedAt, commentJson
            ) VALUES (
                @issueUuid, @projectId, @page, @retrievalDate, @retrievedAt, @commentJson
            );";

            foreach (var comment in comments)
            {
                using var cmd = new SqlCommand(ins, conn, transaction);
                cmd.Parameters.AddWithValue("@issueUuid", comment["issueUuid"] ?? DBNull.Value);
                cmd.Parameters.AddWithValue("@projectId", comment["projectId"] ?? DBNull.Value);
                cmd.Parameters.AddWithValue("@page", comment["page"] ?? DBNull.Value);
                cmd.Parameters.AddWithValue("@retrievalDate", comment["retrievalDate"] ?? DBNull.Value);
                cmd.Parameters.AddWithValue("@retrievedAt", comment["retrievedAt"] ?? DateTime.Now);
                cmd.Parameters.AddWithValue("@commentJson", comment["commentJson"] ?? "");
                cmd.ExecuteNonQuery();
            }

            transaction.Commit();
            Log.Information("Inserted {Count} comment pages into tblReviztoIssueComments.", comments.Count);
        }
        catch (Exception ex)
        {
            transaction.Rollback();
            Log.Error(ex, "Error inserting issue comments.");
            throw;
        }
    }

        // New: Truncate issues table
        public void TruncateReviztoProjectIssues()
            => ExecuteWithConnection(conn =>
            {
                using var cmd = new SqlCommand("TRUNCATE TABLE tblReviztoProjectIssues;", conn);
                cmd.ExecuteNonQuery();
                Log.Information("tblReviztoProjectIssues truncated.");
            });

        // New: Insert issues
        public void InsertReviztoProjectIssues(List<IReadOnlyDictionary<string, object?>> issues)
        {
            if (issues == null || issues.Count == 0)
                return;

            using var conn = new SqlConnection(_connectionString);
            conn.Open();
            using var transaction = conn.BeginTransaction();

            try
            {
                // Delete existing issues per project
                var projectUuids = issues
                    .Select(i => i["projectUuid"])
                    .Where(v => v is Guid)
                    .Cast<Guid>()
                    .Distinct()
                    .ToList();

                foreach (var projUuid in projectUuids)
                {
                    using var del = new SqlCommand("DELETE FROM tblReviztoProjectIssues WHERE projectUuid = @projUuid", conn, transaction);
                    del.Parameters.AddWithValue("@projUuid", projUuid);
                    var d = del.ExecuteNonQuery();
                    Log.Information($"Deleted {d} existing issues for project {projUuid}.");
                }

                const string ins = @"INSERT INTO tblReviztoProjectIssues (
                    issueId, projectUuid, issueJson
                ) VALUES (
                    @issueId, @projUuid, @issueJson
                );";
                int totalInserted = 0;
                foreach (var issue in issues)
                {
                    var issueId = issue.GetValue("issueId") ?? DBNull.Value;
                    var projUuid = issue.GetValue("projectUuid") ?? DBNull.Value;
                    var issueJson = issue.GetValue("issueJson")?.ToString() ?? string.Empty;

                    using var cmd = new SqlCommand(ins, conn, transaction);
                    cmd.Parameters.AddWithValue("@issueId", issueId);
                    cmd.Parameters.AddWithValue("@projUuid", projUuid);
                    cmd.Parameters.AddWithValue("@issueJson", issueJson);
                    cmd.ExecuteNonQuery();
                    totalInserted++;
                }

                transaction.Commit();
                Log.Information($"Inserted {issues.Count} issues into tblReviztoProjectIssues.");
            }
            catch (Exception ex)
            {
                transaction.Rollback();
                Log.Error(ex, "Error inserting Revizto project issues.");
                throw;
            }
        }
        
        public List<Dictionary<string, object>> GetIssuesFromView(int projectId)
            {
                var results = new List<Dictionary<string, object>>();
                using var conn = new SqlConnection(_connectionString);
                conn.Open();

                const string query = @"
                    SELECT uuid
                    FROM dbo.vw_ReviztoProjectIssues_Deconstructed
                    WHERE projectUuid = (SELECT projectUuid FROM tblReviztoProjects WHERE projectId = @projectId)";

                using var cmd = new SqlCommand(query, conn);
                cmd.Parameters.AddWithValue("@projectId", projectId);
                using var reader = cmd.ExecuteReader();

                while (reader.Read())
                {
                    results.Add(new Dictionary<string, object> {
                        { "uuid", reader["uuid"] }
                    });
                }

                return results;
            }

        public int GetProjectIdByUuid(Guid projectUuid)
        {
            using var conn = new SqlConnection(_connectionString);
            conn.Open();

            using var cmd = new SqlCommand("SELECT TOP 1 projectId FROM tblReviztoProjects WHERE projectUuid = @uuid", conn);
            cmd.Parameters.AddWithValue("@uuid", projectUuid);

            var result = cmd.ExecuteScalar();
            return result != null ? Convert.ToInt32(result) : -1;
        }

        private void ExecuteWithConnection(Action<SqlConnection> action)
        {
            if (string.IsNullOrWhiteSpace(_connectionString))
                throw new InvalidOperationException("Connection string not initialized.");
            using var conn = new SqlConnection(_connectionString);
            conn.Open();
            action(conn);
        }
    }
}
