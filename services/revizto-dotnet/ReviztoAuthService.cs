using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using System.Security.Cryptography;
using System.Text;
using Serilog;
using Newtonsoft.Json.Linq;

namespace ReviztoDataExporter
{
    public class ReviztoAuthService
    {
        private readonly string _baseUrl;
        private readonly string _configPath;
        private readonly HttpClient _httpClient;

        public ReviztoAuthService(string baseUrl, string configPath = "appsettings.json")
        {
            _baseUrl = baseUrl?.TrimEnd('/') ?? throw new ArgumentNullException(nameof(baseUrl));
            // Ensure we always use the executable base directory for configuration
            var path = configPath ?? throw new ArgumentNullException(nameof(configPath));
            _configPath = System.IO.Path.IsPathRooted(path)
                ? path
                : System.IO.Path.Combine(AppContext.BaseDirectory, path);
            _httpClient = new HttpClient();
        }

        /// <summary>
        /// Performs initial authentication using API key to get OAuth2 tokens
        /// </summary>
        public async Task<AuthenticationResult> AuthenticateWithApiKey(string apiKey)
        {
            Log.Information("Starting authentication with API key...");

            try
            {
                // Step 1: Exchange API key for OAuth2 tokens
                var tokenResponse = await ExchangeApiKeyForTokens(apiKey);
                
                if (tokenResponse == null)
                {
                    return new AuthenticationResult 
                    { 
                        Success = false, 
                        ErrorMessage = "Failed to exchange API key for tokens" 
                    };
                }

                // Step 2: Validate tokens by making a test API call
                var userInfo = await ValidateTokens(tokenResponse.AccessToken);
                if (userInfo == null)
                {
                    return new AuthenticationResult 
                    { 
                        Success = false, 
                        ErrorMessage = "Token validation failed" 
                    };
                }

                // Step 3: Save tokens to configuration
                await SaveTokensToConfig(tokenResponse);

                Log.Information("Authentication successful for user: {Email}", userInfo.Email);

                return new AuthenticationResult
                {
                    Success = true,
                    AccessToken = tokenResponse.AccessToken,
                    RefreshToken = tokenResponse.RefreshToken,
                    UserInfo = userInfo
                };
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Authentication failed");
                return new AuthenticationResult 
                { 
                    Success = false, 
                    ErrorMessage = ex.Message 
                };
            }
        }

        /// <summary>
        /// Recommended by Revizto: Accept a one-time Access Code (opaque def502...) and exchange for Access + Refresh tokens.
        /// Uses POST (new method) and falls back to GET (legacy method) per Revizto docs.
        /// </summary>
        public async Task<AuthenticationResult> AuthenticateWithAccessCode(string accessCode)
        {
            Log.Information("Starting authentication with access code (authorization_code flow)...");

            try
            {
                var tokens = await TryGetTokensWithAuthorizationCode(accessCode);
                if (tokens == null)
                {
                    return new AuthenticationResult
                    {
                        Success = false,
                        ErrorMessage = "Access code was rejected by server"
                    };
                }

                // Validate tokens (optional) and save
                var userInfo = await ValidateTokens(tokens.AccessToken);
                await SaveTokensToConfig(tokens);

                Log.Information("Authentication via access code succeeded");
                return new AuthenticationResult
                {
                    Success = true,
                    AccessToken = tokens.AccessToken,
                    RefreshToken = tokens.RefreshToken,
                    UserInfo = userInfo
                };
            }
            catch (RegionMismatchException rme)
            {
                Log.Error(rme, "Region mismatch while exchanging access code");
                return new AuthenticationResult
                {
                    Success = false,
                    ErrorMessage = "Region mismatch (-205). Obtain an access code in the current region or update BaseUrl to match the region where the code was issued."
                };
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Authentication with access code failed");
                return new AuthenticationResult
                {
                    Success = false,
                    ErrorMessage = ex.Message
                };
            }
        }

        private async Task<TokenResponse?> TryGetTokensWithAuthorizationCode(string accessCode)
        {
            // 1) New method: POST with grant_type=authorization_code & code
            try
            {
                var form = new Dictionary<string, string>
                {
                    { "grant_type", "authorization_code" },
                    { "code", accessCode }
                };
                var request = new HttpRequestMessage(HttpMethod.Post, $"{_baseUrl}/v5/oauth2")
                {
                    Content = new FormUrlEncodedContent(form)
                };
                request.Headers.Add("Accept", "application/json");

                var response = await _httpClient.SendAsync(request);
                var content = await response.Content.ReadAsStringAsync();
                if (response.IsSuccessStatusCode)
                {
                    return ParseTokenResponse(content);
                }
                else
                {
                    // Detect Revizto error codes to provide guidance
                    if (TryGetReviztoErrorCode(content, out var code) && code == -205)
                        throw new RegionMismatchException("Access code region mismatch (-205)");
                    Log.Warning("authorization_code POST failed. Status: {Status}, Content: {Content}", response.StatusCode, content);
                }
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Exception during authorization_code POST");
            }

            // 2) Legacy method: GET /v5/oauth2?code={access_code}
            try
            {
                var url = $"{_baseUrl}/v5/oauth2?code={Uri.EscapeDataString(accessCode)}";
                var request = new HttpRequestMessage(HttpMethod.Get, url);
                request.Headers.Add("Accept", "application/json");
                var response = await _httpClient.SendAsync(request);
                var content = await response.Content.ReadAsStringAsync();
                if (response.IsSuccessStatusCode)
                {
                    return ParseTokenResponse(content);
                }
                else
                {
                    if (TryGetReviztoErrorCode(content, out var code) && code == -205)
                        throw new RegionMismatchException("Access code region mismatch (-205)");
                    Log.Warning("authorization_code GET failed. Status: {Status}, Content: {Content}", response.StatusCode, content);
                }
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Exception during authorization_code GET");
            }

            return null;
        }

        private TokenResponse? ParseTokenResponse(string content)
        {
            try
            {
                var json = JObject.Parse(content);
                var accessToken = json["access_token"]?.ToString();
                var refreshToken = json["refresh_token"]?.ToString();
                var expiresIn = json["expires_in"]?.ToObject<int>() ?? 3600;

                if (!string.IsNullOrEmpty(accessToken))
                {
                    return new TokenResponse
                    {
                        AccessToken = accessToken,
                        RefreshToken = refreshToken ?? "",
                        ExpiresIn = expiresIn
                    };
                }
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Failed to parse token response");
            }
            return null;
        }

        private bool TryGetReviztoErrorCode(string content, out int code)
        {
            code = 0;
            try
            {
                var json = JObject.Parse(content);
                var result = json["result"]?.ToObject<int?>();
                if (result.HasValue)
                {
                    code = result.Value;
                    return true;
                }
            }
            catch { }
            return false;
        }
        /// <summary>
        /// Accept a user-provided Access Token, validate it, and attempt to obtain a Refresh Token via RFC 8693 Token Exchange.
        /// If the server does not support exchange, we still store and use the access token until expiry.
        /// </summary>
        public async Task<AuthenticationResult> AuthenticateWithAccessToken(string accessToken)
        {
            Log.Information("Starting authentication with provided access token...");

            try
            {
                // Try token exchange first (some servers issue opaque tokens that don't validate at /v5/user directly)
                TokenResponse? exchanged = await TryExchangeAccessTokenForRefresh(accessToken);

                if (exchanged != null && !string.IsNullOrEmpty(exchanged.RefreshToken))
                {
                    // Save full token set
                    await SaveTokensToConfig(exchanged);
                    Log.Information("Access token exchange succeeded - refresh token obtained");
                    // Validate final access token for user info (best-effort)
                    var ui = await ValidateTokens(exchanged.AccessToken);
                    return new AuthenticationResult
                    {
                        Success = true,
                        AccessToken = exchanged.AccessToken,
                        RefreshToken = exchanged.RefreshToken,
                        UserInfo = ui
                    };
                }

                // If exchange did not work, try validating the provided token directly
                var userInfo = await ValidateTokens(accessToken);
                if (userInfo != null)
                {
                    // Save only the access token (no refresh)
                    await SaveAccessTokenOnly(accessToken);
                    Log.Warning("Token exchange did not yield a refresh token; proceeding with access token only");
                    return new AuthenticationResult
                    {
                        Success = true,
                        AccessToken = accessToken,
                        RefreshToken = null,
                        UserInfo = userInfo
                    };
                }

                // Neither exchange nor direct validation worked
                return new AuthenticationResult
                {
                    Success = false,
                    ErrorMessage = "Access token rejected by server for both validation and exchange"
                };
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Authentication with access token failed");
                return new AuthenticationResult
                {
                    Success = false,
                    ErrorMessage = ex.Message
                };
            }
        }

        /// <summary>
        /// Checks if current tokens are valid and not expired
        /// </summary>
        public async Task<bool> ValidateCurrentTokens()
        {
            try
            {
                var tokens = LoadTokensFromConfig();
                if (tokens == null) 
                {
                    Log.Information("No tokens found in configuration");
                    return false;
                }

                // Proactively check expiration to avoid unnecessary calls
                if (IsTokenExpired(tokens.AccessToken))
                {
                    Log.Information("Stored access token is expired or near expiry");
                    return false;
                }

                Log.Information("Testing token validation by making API call...");
                var userInfo = await ValidateTokens(tokens.AccessToken);
                if (userInfo != null)
                {
                    Log.Information("Tokens are valid - API call successful for user: {UserEmail}", userInfo.Email);
                    return true;
                }
                else
                {
                    Log.Warning("Token validation failed - API call returned null");
                    return false;
                }
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Token validation failed");
                return false;
            }
        }

        /// <summary>
        /// Checks if a JWT token is expired
        /// </summary>
        public bool IsTokenExpired(string jwtToken)
        {
            if (string.IsNullOrEmpty(jwtToken)) return true;

            try
            {
                var parts = jwtToken.Split('.');
                if (parts.Length != 3) return true;

                var payload = parts[1];
                
                // Add padding if needed
                var paddingLength = (4 - payload.Length % 4) % 4;
                payload += new string('=', paddingLength);

                var decoded = Convert.FromBase64String(payload);
                var json = Encoding.UTF8.GetString(decoded);
                
                using var document = JsonDocument.Parse(json);
                var root = document.RootElement;

                if (root.TryGetProperty("exp", out var expElement))
                {
                    long exp;
                    
                    // Handle both integer and decimal representations
                    if (expElement.ValueKind == JsonValueKind.Number)
                    {
                        if (expElement.TryGetInt64(out exp))
                        {
                            // exp is already an integer timestamp
                        }
                        else if (expElement.TryGetDouble(out var expDouble))
                        {
                            // exp is a decimal, convert to integer
                            exp = (long)expDouble;
                        }
                        else
                        {
                            Log.Warning("Unable to parse exp claim as number: {ExpValue}", expElement);
                            return true;
                        }
                    }
                    else
                    {
                        Log.Warning("Exp claim is not a number: {ExpValue}", expElement);
                        return true;
                    }
                    
                    var expDate = DateTimeOffset.FromUnixTimeSeconds(exp).DateTime;
                    var isExpired = DateTime.UtcNow >= expDate.AddMinutes(-5); // 5 minute buffer
                    
                    Log.Debug("Token expires at {ExpirationDate} (UTC), Current time: {CurrentTime} (UTC), Is expired: {IsExpired}", 
                        expDate, DateTime.UtcNow, isExpired);
                    
                    return isExpired;
                }

                Log.Warning("JWT token missing exp claim");
                return true; // If no exp claim, consider expired
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Failed to parse JWT token expiration");
                return true;
            }
        }

        private async Task<TokenResponse?> ExchangeApiKeyForTokens(string apiKey)
        {
            // Try different grant types that Revizto might support
            var grantTypes = new[] 
            {
                ("api_key", "api_key"),
                ("client_credentials", "client_secret"),  
                ("password", "api_key")  // Sometimes API keys are used as passwords
            };

            Exception? lastException = null;
            
            foreach (var (grantType, keyParam) in grantTypes)
            {
                try
                {
                    var request = new HttpRequestMessage(HttpMethod.Post, $"{_baseUrl}/v5/oauth2")
                    {
                        Content = new FormUrlEncodedContent(new Dictionary<string, string>
                        {
                            { "grant_type", grantType },
                            { keyParam, apiKey }
                        })
                    };

                    request.Headers.Add("Accept", "application/json");
                    
                    Log.Information("Trying grant type: {GrantType} with parameter: {KeyParam}", grantType, keyParam);
                    
                    var response = await _httpClient.SendAsync(request);
                    var content = await response.Content.ReadAsStringAsync();

                    if (response.IsSuccessStatusCode)
                    {
                        Log.Information("Successfully exchanged API key using grant_type: {GrantType}", grantType);
                        
                        var json = JObject.Parse(content);
                        
                        var accessToken = json["access_token"]?.ToString();
                        var refreshToken = json["refresh_token"]?.ToString();
                        var expiresIn = json["expires_in"]?.ToObject<int>() ?? 3600;

                        if (string.IsNullOrEmpty(accessToken) || string.IsNullOrEmpty(refreshToken))
                        {
                            Log.Warning("Response missing tokens for grant_type {GrantType}: {Content}", grantType, content);
                            continue;
                        }

                        return new TokenResponse
                        {
                            AccessToken = accessToken,
                            RefreshToken = refreshToken,
                            ExpiresIn = expiresIn
                        };
                    }
                    else
                    {
                        Log.Warning("Grant type {GrantType} failed. Status: {StatusCode}, Response: {Content}", 
                            grantType, response.StatusCode, content);
                        lastException = new Exception($"Grant type {grantType} failed: {response.StatusCode} - {content}");
                    }
                }
                catch (Exception ex)
                {
                    Log.Warning(ex, "Exception with grant_type {GrantType}", grantType);
                    lastException = ex;
                }
            }

            Log.Error("All authentication methods failed. Last exception: {Exception}", lastException?.Message);
            throw lastException ?? new Exception("All authentication methods failed");
        }

        private async Task<UserInfo?> ValidateTokens(string accessToken)
        {
            try
            {
                var request = new HttpRequestMessage(HttpMethod.Get, $"{_baseUrl}/v5/user");
                request.Headers.Add("Authorization", $"Bearer {accessToken}");
                request.Headers.Add("Accept", "application/json");

                var response = await _httpClient.SendAsync(request);
                var content = await response.Content.ReadAsStringAsync();

                if (!response.IsSuccessStatusCode)
                {
                    Log.Warning("Token validation failed. Status: {StatusCode}, Content: {Content}", 
                        response.StatusCode, content);
                    return null;
                }

                var json = JObject.Parse(content);
                var data = json["data"] as JObject;
                
                if (data != null)
                {
                    return new UserInfo
                    {
                        Id = data["id"]?.ToObject<int>() ?? 0,
                        Email = data["email"]?.ToString() ?? "",
                        Name = data["name"]?.ToString() ?? ""
                    };
                }

                return null;
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Token validation error");
                return null;
            }
        }

        private async Task SaveTokensToConfig(TokenResponse tokens)
        {
            try
            {
                if (!File.Exists(_configPath))
                {
                    Log.Warning("Configuration file not found: {ConfigPath}", _configPath);
                    return;
                }

                var configJson = JObject.Parse(await File.ReadAllTextAsync(_configPath));

                if (configJson["ReviztoAPI"] == null)
                {
                    configJson["ReviztoAPI"] = new JObject();
                }

                var reviztoSection = configJson["ReviztoAPI"] as JObject;
                if (reviztoSection != null)
                {
                    reviztoSection["AccessToken"] = tokens.AccessToken;
                    // Only overwrite refresh token if provided
                    if (!string.IsNullOrEmpty(tokens.RefreshToken))
                    {
                        reviztoSection["RefreshToken"] = tokens.RefreshToken;
                    }
                    reviztoSection["TokenUpdatedAt"] = DateTimeOffset.UtcNow.ToString("O");
                    
                    await File.WriteAllTextAsync(_configPath, configJson.ToString());
                    Log.Information("Tokens saved to configuration file");
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to save tokens to configuration");
                throw;
            }
        }

        private async Task SaveAccessTokenOnly(string accessToken)
        {
            try
            {
                if (!File.Exists(_configPath))
                {
                    Log.Warning("Configuration file not found: {ConfigPath}", _configPath);
                    return;
                }

                var configJson = JObject.Parse(await File.ReadAllTextAsync(_configPath));

                if (configJson["ReviztoAPI"] == null)
                {
                    configJson["ReviztoAPI"] = new JObject();
                }

                var reviztoSection = configJson["ReviztoAPI"] as JObject;
                if (reviztoSection != null)
                {
                    reviztoSection["AccessToken"] = accessToken;
                    reviztoSection["TokenUpdatedAt"] = DateTimeOffset.UtcNow.ToString("O");

                    await File.WriteAllTextAsync(_configPath, configJson.ToString());
                    Log.Information("Access token saved to configuration file (no refresh token)");
                }
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to save access token to configuration");
                throw;
            }
        }

        private async Task<TokenResponse?> TryExchangeAccessTokenForRefresh(string accessToken)
        {
            // Try several token exchange request variants (server-dependent)
            var formAttempts = new List<Dictionary<string, string>>
            {
                // RFC 8693 with explicit refresh token request
                new()
                {
                    { "grant_type", "urn:ietf:params:oauth:grant-type:token-exchange" },
                    { "subject_token", accessToken },
                    { "subject_token_type", "urn:ietf:params:oauth:token-type:access_token" },
                    { "requested_token_type", "refresh_token" }
                },
                // RFC 8693 without requested_token_type (let server decide)
                new()
                {
                    { "grant_type", "urn:ietf:params:oauth:grant-type:token-exchange" },
                    { "subject_token", accessToken },
                    { "subject_token_type", "urn:ietf:params:oauth:token-type:access_token" }
                },
                // Non-standard possibilities some servers use
                new()
                {
                    { "grant_type", "token_exchange" },
                    { "subject_token", accessToken },
                    { "subject_token_type", "access_token" }
                },
                // Some servers treat portal token as api_key in a form body
                new()
                {
                    { "grant_type", "api_key" },
                    { "api_key", accessToken }
                }
            };

            foreach (var form in formAttempts)
            {
                try
                {
                    var request = new HttpRequestMessage(HttpMethod.Post, $"{_baseUrl}/v5/oauth2")
                    {
                        Content = new FormUrlEncodedContent(form)
                    };
                    request.Headers.Add("Accept", "application/json");

                    Log.Information("Attempting token exchange flow: grant_type={Grant}", form["grant_type"]);
                    var response = await _httpClient.SendAsync(request);
                    var content = await response.Content.ReadAsStringAsync();

                    if (!response.IsSuccessStatusCode)
                    {
                        Log.Warning("Token exchange attempt failed. Status: {Status}, Response: {Content}", response.StatusCode, content);
                        continue;
                    }

                    var json = JObject.Parse(content);
                    var newAccess = json["access_token"]?.ToString();
                    var newRefresh = json["refresh_token"]?.ToString();
                    var expiresIn = json["expires_in"]?.ToObject<int>() ?? 3600;

                    if (!string.IsNullOrEmpty(newAccess) || !string.IsNullOrEmpty(newRefresh))
                    {
                        // If only refresh is returned, keep old access; otherwise adopt new
                        return new TokenResponse
                        {
                            AccessToken = !string.IsNullOrEmpty(newAccess) ? newAccess : accessToken,
                            RefreshToken = newRefresh ?? "",
                            ExpiresIn = expiresIn
                        };
                    }
                }
                catch (Exception ex)
                {
                    Log.Warning(ex, "Exception during token exchange attempt");
                }
            }

            // Header-based attempts, some servers expect API key in headers
            var headerCombos = new List<(string Name, string Value)>
            {
                ("x-api-key", accessToken),
                ("X-API-Key", accessToken),
                ("ApiKey", accessToken),
                ("Authorization", $"Bearer {accessToken}")
            };

            foreach (var header in headerCombos)
            {
                try
                {
                    var request = new HttpRequestMessage(HttpMethod.Post, $"{_baseUrl}/v5/oauth2")
                    {
                        Content = new FormUrlEncodedContent(new Dictionary<string, string>
                        {
                            { "grant_type", "api_key" }
                        })
                    };
                    request.Headers.Add("Accept", "application/json");
                    request.Headers.Remove(header.Name);
                    request.Headers.Add(header.Name, header.Value);

                    Log.Information("Attempting token exchange with header {HeaderName}", header.Name);
                    var response = await _httpClient.SendAsync(request);
                    var content = await response.Content.ReadAsStringAsync();

                    if (!response.IsSuccessStatusCode)
                    {
                        Log.Warning("Header-based token exchange failed. Status: {Status}, Response: {Content}", response.StatusCode, content);
                        continue;
                    }

                    var json = JObject.Parse(content);
                    var newAccess = json["access_token"]?.ToString();
                    var newRefresh = json["refresh_token"]?.ToString();
                    var expiresIn = json["expires_in"]?.ToObject<int>() ?? 3600;
                    if (!string.IsNullOrEmpty(newAccess) || !string.IsNullOrEmpty(newRefresh))
                    {
                        return new TokenResponse
                        {
                            AccessToken = !string.IsNullOrEmpty(newAccess) ? newAccess : accessToken,
                            RefreshToken = newRefresh ?? "",
                            ExpiresIn = expiresIn
                        };
                    }
                }
                catch (Exception ex)
                {
                    Log.Warning(ex, "Exception during header-based token exchange attempt");
                }
            }

            // JSON body attempts
            var jsonBodies = new List<JObject>
            {
                new JObject
                {
                    ["grant_type"] = "api_key",
                    ["api_key"] = accessToken
                },
                new JObject
                {
                    ["grant_type"] = "urn:ietf:params:oauth:grant-type:token-exchange",
                    ["subject_token"] = accessToken,
                    ["subject_token_type"] = "urn:ietf:params:oauth:token-type:access_token",
                    ["requested_token_type"] = "refresh_token"
                }
            };

            foreach (var body in jsonBodies)
            {
                try
                {
                    var request = new HttpRequestMessage(HttpMethod.Post, $"{_baseUrl}/v5/oauth2")
                    {
                        Content = new StringContent(body.ToString(), Encoding.UTF8, "application/json")
                    };
                    request.Headers.Add("Accept", "application/json");

                    Log.Information("Attempting JSON token exchange flow: {Grant}", body["grant_type"]?.ToString());
                    var response = await _httpClient.SendAsync(request);
                    var content = await response.Content.ReadAsStringAsync();
                    if (!response.IsSuccessStatusCode)
                    {
                        Log.Warning("JSON token exchange failed. Status: {Status}, Response: {Content}", response.StatusCode, content);
                        continue;
                    }
                    var json = JObject.Parse(content);
                    var newAccess = json["access_token"]?.ToString();
                    var newRefresh = json["refresh_token"]?.ToString();
                    var expiresIn = json["expires_in"]?.ToObject<int>() ?? 3600;
                    if (!string.IsNullOrEmpty(newAccess) || !string.IsNullOrEmpty(newRefresh))
                    {
                        return new TokenResponse
                        {
                            AccessToken = !string.IsNullOrEmpty(newAccess) ? newAccess : accessToken,
                            RefreshToken = newRefresh ?? "",
                            ExpiresIn = expiresIn
                        };
                    }
                }
                catch (Exception ex)
                {
                    Log.Warning(ex, "Exception during JSON token exchange attempt");
                }
            }

            return null;
        }

        private TokenResponse? LoadTokensFromConfig()
        {
            try
            {
                if (!File.Exists(_configPath)) return null;

                var configJson = JObject.Parse(File.ReadAllText(_configPath));
                var reviztoSection = configJson["ReviztoAPI"];

                if (reviztoSection == null) return null;

                var accessToken = reviztoSection["AccessToken"]?.ToString();
                var refreshToken = reviztoSection["RefreshToken"]?.ToString();

                if (string.IsNullOrEmpty(accessToken) || string.IsNullOrEmpty(refreshToken))
                    return null;

                return new TokenResponse
                {
                    AccessToken = accessToken,
                    RefreshToken = refreshToken
                };
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Failed to load tokens from configuration");
                return null;
            }
        }

        public void Dispose()
        {
            _httpClient?.Dispose();
        }
    }

    public class RegionMismatchException : Exception
    {
        public RegionMismatchException(string message) : base(message) { }
    }

    public class AuthenticationResult
    {
        public bool Success { get; set; }
        public string? ErrorMessage { get; set; }
        public string? AccessToken { get; set; }
        public string? RefreshToken { get; set; }
        public UserInfo? UserInfo { get; set; }
    }

    public class TokenResponse
    {
        public string AccessToken { get; set; } = "";
        public string RefreshToken { get; set; } = "";
        public int ExpiresIn { get; set; }
    }

    public class UserInfo
    {
        public int Id { get; set; }
        public string Email { get; set; } = "";
        public string Name { get; set; } = "";
    }
}