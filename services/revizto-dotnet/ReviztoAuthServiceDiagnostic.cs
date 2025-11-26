using System;
using System.IO;
using System.Text;
using System.Text.Json;
using Newtonsoft.Json.Linq;
using Serilog;

namespace ReviztoDataExporter
{
    public class ReviztoAuthServiceDiagnostic
    {
        private readonly string _baseUrl;
        private readonly ILogger _logger;

        public ReviztoAuthServiceDiagnostic(string baseUrl)
        {
            _baseUrl = baseUrl;
            _logger = Log.ForContext<ReviztoAuthServiceDiagnostic>();
        }

        public bool IsTokenExpired(string accessToken)
        {
            _logger.Information("Starting token expiration check");
            
            if (string.IsNullOrEmpty(accessToken))
            {
                _logger.Warning("Access token is null or empty - treating as expired");
                return true;
            }

            try
            {
                _logger.Debug("Parsing JWT token structure");
                var parts = accessToken.Split('.');
                if (parts.Length != 3)
                {
                    _logger.Warning("Invalid JWT format - expected 3 parts, got {PartCount}", parts.Length);
                    return true;
                }

                // Decode the payload
                var payload = parts[1];
                
                // Add padding if necessary
                var padding = 4 - (payload.Length % 4);
                if (padding != 4)
                {
                    payload += new string('=', padding);
                }

                _logger.Debug("Decoding JWT payload");
                var decodedPayload = Convert.FromBase64String(payload);
                var payloadJson = Encoding.UTF8.GetString(decodedPayload);
                
                _logger.Debug("Payload JSON: {PayloadJson}", payloadJson);

                var payloadObj = JsonDocument.Parse(payloadJson);
                
                if (!payloadObj.RootElement.TryGetProperty("exp", out var expElement))
                {
                    _logger.Warning("JWT token missing 'exp' claim - treating as expired");
                    return true;
                }

                // Handle both integer and decimal timestamps
                double expValue;
                if (expElement.ValueKind == JsonValueKind.Number)
                {
                    if (expElement.TryGetDouble(out expValue))
                    {
                        _logger.Debug("Parsed expiration timestamp as double: {ExpValue}", expValue);
                    }
                    else if (expElement.TryGetInt64(out var expInt))
                    {
                        expValue = expInt;
                        _logger.Debug("Parsed expiration timestamp as integer: {ExpValue}", expValue);
                    }
                    else
                    {
                        _logger.Warning("Unable to parse expiration timestamp as number");
                        return true;
                    }
                }
                else
                {
                    _logger.Warning("Expiration claim is not a number: {ExpValueKind}", expElement.ValueKind);
                    return true;
                }

                var expirationTime = DateTimeOffset.FromUnixTimeSeconds((long)expValue);
                var now = DateTimeOffset.UtcNow;
                var buffer = TimeSpan.FromMinutes(5); // Refresh 5 minutes before expiry

                var timeUntilExpiry = expirationTime - now;
                var shouldRefresh = timeUntilExpiry <= buffer;

                _logger.Information("Token expiration analysis: " +
                    "Current time: {CurrentTime}, " +
                    "Token expires: {ExpirationTime}, " +
                    "Time until expiry: {TimeUntilExpiry}, " +
                    "Buffer: {Buffer}, " +
                    "Should refresh: {ShouldRefresh}",
                    now.ToString("yyyy-MM-dd HH:mm:ss UTC"),
                    expirationTime.ToString("yyyy-MM-dd HH:mm:ss UTC"),
                    timeUntilExpiry.ToString(@"dd\:hh\:mm\:ss"),
                    buffer.ToString(@"hh\:mm\:ss"),
                    shouldRefresh);

                return shouldRefresh;
            }
            catch (Exception ex)
            {
                _logger.Error(ex, "Error parsing JWT token - treating as expired");
                return true;
            }
        }

        public void AnalyzeTokenFromConfig(string configPath = "appsettings.json")
        {
            try
            {
                _logger.Information("Analyzing token from configuration file: {ConfigPath}", configPath);
                
                if (!File.Exists(configPath))
                {
                    _logger.Error("Configuration file not found: {ConfigPath}", configPath);
                    return;
                }

                var configContent = File.ReadAllText(configPath);
                var config = JObject.Parse(configContent);
                
                var accessToken = config["ReviztoAPI"]?["AccessToken"]?.ToString();
                var refreshToken = config["ReviztoAPI"]?["RefreshToken"]?.ToString();
                var baseUrl = config["ReviztoAPI"]?["BaseUrl"]?.ToString();

                _logger.Information("Configuration analysis: " +
                    "Has AccessToken: {HasAccessToken}, " +
                    "Has RefreshToken: {HasRefreshToken}, " +
                    "BaseUrl: {BaseUrl}",
                    !string.IsNullOrEmpty(accessToken),
                    !string.IsNullOrEmpty(refreshToken),
                    baseUrl);

                if (!string.IsNullOrEmpty(accessToken))
                {
                    var isExpired = IsTokenExpired(accessToken);
                    _logger.Information("Current access token status: {TokenStatus}",
                        isExpired ? "EXPIRED/NEEDS_REFRESH" : "VALID");
                }
                else
                {
                    _logger.Warning("No access token found in configuration");
                }
            }
            catch (Exception ex)
            {
                _logger.Error(ex, "Error analyzing configuration file");
            }
        }

        public void LogTokenRefreshAttempt(string reason)
        {
            _logger.Information("Token refresh attempt initiated. Reason: {Reason}, Timestamp: {Timestamp}",
                reason, DateTimeOffset.UtcNow.ToString("yyyy-MM-dd HH:mm:ss.fff UTC"));
        }

        public void LogTokenRefreshResult(bool success, string? details = null)
        {
            if (success)
            {
                _logger.Information("Token refresh successful. Details: {Details}", details ?? "No additional details");
            }
            else
            {
                _logger.Error("Token refresh failed. Details: {Details}", details ?? "No additional details");
            }
        }
    }
}