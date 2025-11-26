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
        // Read configuration from appsettings.json in the executable directory
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

        // First check if current access token is actually expired
        var authService = new ReviztoAuthService(_baseUrl);
        if (!authService.IsTokenExpired(GetCurrentAccessToken()))
        {
            Log.Information("Access token is still valid, no refresh needed");
            return GetCurrentAccessToken();
        }

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
            
            // Check if it's a "Forbidden" error which likely means refresh token is expired
            if (response.StatusCode == System.Net.HttpStatusCode.Forbidden)
            {
                Log.Error("Refresh token appears to be expired or invalid. Re-authentication required.");
                throw new RefreshTokenExpiredException("Refresh token expired. Please re-authenticate with API key.");
            }
            
            throw new Exception($"Failed to refresh access token. Status code: {response.StatusCode}");
        }

        var json = JObject.Parse(content);

        string? newAccessToken = json["access_token"]?.ToString();
        string? newRefreshToken = json["refresh_token"]?.ToString();

        if (string.IsNullOrEmpty(newAccessToken))
        {
            Log.Error("Received invalid or incomplete token response during refresh - missing access_token.");
            throw new Exception("Invalid token response received during refresh - missing access_token.");
        }

        // Handle token rotation - if new refresh token is provided, use it; otherwise keep the old one
        var refreshTokenToUse = !string.IsNullOrEmpty(newRefreshToken) ? newRefreshToken : _refreshToken;
        
        UpdateTokens(newAccessToken, refreshTokenToUse);
        Log.Information("Access token successfully refreshed. New refresh token provided: {NewRefreshTokenProvided}", !string.IsNullOrEmpty(newRefreshToken));

        return newAccessToken;
    }

    private void UpdateTokens(string accessToken, string refreshToken)
    {
        try
        {
            // Always update the config in the executable directory
            var configPath = Path.Combine(AppContext.BaseDirectory, "appsettings.json");
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

    private string GetCurrentAccessToken()
    {
        try
        {
            var configPath = Path.Combine(AppContext.BaseDirectory, "appsettings.json");
            if (!File.Exists(configPath)) return "";

            var configJson = JObject.Parse(File.ReadAllText(configPath));
            return configJson["ReviztoAPI"]?["AccessToken"]?.ToString() ?? "";
        }
        catch
        {
            return "";
        }
    }
}

public class RefreshTokenExpiredException : Exception
{
    public RefreshTokenExpiredException(string message) : base(message) { }
    public RefreshTokenExpiredException(string message, Exception innerException) : base(message, innerException) { }
}
