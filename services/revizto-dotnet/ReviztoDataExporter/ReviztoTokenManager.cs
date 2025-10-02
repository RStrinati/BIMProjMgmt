using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading.Tasks;
using Serilog;
using ReviztoDataExporter;

public class ReviztoTokenRefresher
{
    private readonly string _baseUrl;
    private readonly string _refreshToken;

    public ReviztoTokenRefresher()
    {
        // Read configuration from appsettings.json
        var configPath = Path.Combine(AppContext.BaseDirectory, "appsettings.json");
        if (!File.Exists(configPath))
        {
            throw new FileNotFoundException($"Configuration file not found: {configPath}");
        }

        var configJson = JObject.Parse(File.ReadAllText(configPath));
        var reviztoApiSection = configJson["ReviztoAPI"];

        if (reviztoApiSection == null)
        {
            throw new Exception("ReviztoAPI section is missing in appsettings.json");
        }

        _baseUrl = reviztoApiSection["BaseUrl"]?.ToString()?.TrimEnd('/') ?? throw new Exception("BaseUrl is missing in appsettings.json");
        _refreshToken = reviztoApiSection["RefreshToken"]?.ToString() ?? throw new Exception("RefreshToken is missing in appsettings.json");
    }

    public async Task<string> RefreshAccessToken()
    {
        Log.Information("Attempting to refresh access token...");

        using var client = new HttpClient();
        var request = new HttpRequestMessage(HttpMethod.Post, $"{_baseUrl}/v5/oauth2")
        {
            Content = new FormUrlEncodedContent(new Dictionary<string, string>
            {
                { "grant_type", "refresh_token" },
                { "refresh_token", _refreshToken }
            })
        };

        request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

        HttpResponseMessage response;
        try
        {
            response = await client.SendAsync(request);
        }
        catch (Exception ex)
        {
            Log.Error(ex, $"Failed to send token refresh request. URL: {_baseUrl}/v5/oauth2");
            throw new Exception("Error during token refresh request", ex);
        }

        var content = await response.Content.ReadAsStringAsync();

        if (!response.IsSuccessStatusCode)
        {
            Log.Error($"Token refresh failed. Status Code: {response.StatusCode}, Reason: {response.ReasonPhrase}, Response: {content}");
            throw new Exception($"Failed to refresh access token. Status code: {response.StatusCode}");
        }

        var json = JObject.Parse(content);

        string? newAccessToken = json["access_token"]?.ToString();
        string? newRefreshToken = json["refresh_token"]?.ToString();

        if (string.IsNullOrEmpty(newAccessToken) || string.IsNullOrEmpty(newRefreshToken))
        {
            Log.Error("Received invalid or incomplete token response during refresh.");
            throw new Exception("Invalid token response received during refresh.");
        }

        UpdateTokens(newAccessToken, newRefreshToken);
        Log.Information("Access token successfully refreshed.");

        return newAccessToken;
    }

    private void UpdateTokens(string accessToken, string refreshToken)
    {
        try
        {
            var configPath = "appsettings.json";
            if (!File.Exists(configPath))
            {
                Log.Warning($"Configuration file not found: {configPath}. Tokens will not be updated.");
                return;
            }

            var configJson = JObject.Parse(File.ReadAllText(configPath));

            if (configJson["ReviztoAPI"] == null)
            {
                configJson["ReviztoAPI"] = new JObject();
            }

            var reviztoApiSection = configJson["ReviztoAPI"] as JObject;
            if (reviztoApiSection != null)
            {
                reviztoApiSection["AccessToken"] = accessToken;
                reviztoApiSection["RefreshToken"] = refreshToken;

                File.WriteAllText(configPath, configJson.ToString());
                Log.Information("Tokens updated successfully in configuration.");
            }
            else
            {
                Log.Warning("Failed to update tokens: ReviztoAPI section is not a valid JSON object.");
            }
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Failed to update tokens in configuration file.");
            throw new Exception("Error updating tokens in configuration", ex);
        }
    }
}
