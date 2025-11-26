using System;
using System.Net;
using System.Threading.Tasks;
using RestSharp;
using Newtonsoft.Json.Linq;
using Serilog;

namespace ReviztoDataExporter
{
    public class ReviztoApiClient
    {
        private readonly string _baseUrl;
        private string _accessToken;
        private readonly ReviztoTokenRefresher _tokenRefresher;
        private readonly ReviztoAuthService _authService;
        private readonly RestClient _client;

        public ReviztoApiClient(string baseUrl, string accessToken, string refreshToken)
        {
            _baseUrl = baseUrl ?? throw new ArgumentNullException(nameof(baseUrl));
            _accessToken = accessToken ?? throw new ArgumentNullException(nameof(accessToken));
            _tokenRefresher = new ReviztoTokenRefresher();
            _authService = new ReviztoAuthService(baseUrl);

            var options = new RestClientOptions(_baseUrl)
            {
                ThrowOnAnyError = false
            };
            _client = new RestClient(options);
        }

        public async Task<JObject?> GetLicenseTeamMembers(string licenseUuid)
        {
            return await ApiCallHelper.SafeApiCall(
                async () =>
                {
                    var request = new RestRequest($"v5/license/{licenseUuid}/team", Method.Get);
                    var response = await ExecuteRequest(request);

                    if (response["data"] is not JObject data)
                    {
                        Log.Warning("Unexpected team members response: {Response}", response);
                        return new JObject { ["entities"] = new JArray() };
                    }

                    var members = data["entities"] as JArray ?? new JArray();
                    return new JObject { ["entities"] = members };
                },
                $"Fetching team members for license {licenseUuid}"
            );
        }
        public async Task<JObject?> GetProjectIssues(string projectUuid, int page = 0, int limit = 100)
                {
                    return await ApiCallHelper.SafeApiCall(
                        async () =>
                        {
                            var request = new RestRequest($"v5/project/{projectUuid}/issue-filter/filter", Method.Get);
                            request.AddQueryParameter("page", page.ToString());
                            request.AddQueryParameter("limit", limit.ToString());
                            request.AddOrUpdateHeader("Accept", "application/json");
                            return await ExecuteRequest(request);
                        },
                        $"Fetching issues for project {projectUuid}, page {page}"
                    );
                }
        public async Task<JObject?> GetUserLicenses()
            => await ApiCallHelper.SafeApiCall(
                async () => await ExecuteRequest(new RestRequest("v5/user/licenses", Method.Get)),
                "Fetching user licenses"
            );

        /// <summary>
        /// Paged project list by license UUID
        /// </summary>
        public async Task<JObject?> GetProjectsForLicense(string licenseUuid, int page = 0, int limit = 24)
        {
            return await ApiCallHelper.SafeApiCall(
                async () =>
                {
                    var request = new RestRequest($"v5/project/list/{licenseUuid}/paged", Method.Get);
                    request.AddQueryParameter("page", page.ToString());
                    request.AddQueryParameter("limit", limit.ToString());
                    return await ExecuteRequest(request);
                },
                $"Fetching projects for license {licenseUuid}, page {page}"
            );
        }

        public async Task<JObject?> GetCurrentUserInfo()
            => await ApiCallHelper.SafeApiCall(
                async () => await ExecuteRequest(new RestRequest("v5/user", Method.Get)),
                "Fetching current user info"
            );

        public async Task<JObject?> GetProjectByUuid(string region, string projectUuid)
            => await ApiCallHelper.SafeApiCall(
                async () => await ExecuteRequest(new RestRequest($"v5/project/{projectUuid}", Method.Get)),
                $"Fetching project {projectUuid}"
            );

        public async Task<JObject?> GetIssueComments(string issueUuid, int projectId, DateTime fromDate, int page)
            {
                var dateStr = fromDate.ToString("yyyy-MM-dd");
                var url = $"/v5/issue/{issueUuid}/comments/date?projectId={projectId}&date={dateStr}&page={page}";

                Log.Debug("GET {Url}", url);

                var request = new RestRequest(url, Method.Get);
                SetAuthHeader(request);
                var response = await _client.ExecuteAsync(request);

                Log.Debug("Response for comments: {Content}", response.Content);

                if (!response.IsSuccessful)
                {
                    Log.Warning("Failed to fetch comments. Status: {StatusCode}, Content: {Content}", response.StatusCode, response.Content);
                    return null;
                }

                return JObject.Parse(response.Content!);
            }


        internal async Task<JObject> GetProjectsByLicenseId(string region, int licenseId)
        {
            return await ApiCallHelper.SafeApiCall(
                async () =>
                {
                    var request = new RestRequest($"v5/license/{licenseId}/projects", Method.Get);
                    return await ExecuteRequest(request);
                },
                $"Fetching projects for license ID {licenseId} in region {region}"
            ) ?? new JObject();
        }

        private async Task<JObject> ExecuteRequest(RestRequest request)
        {
            // Check token expiration before making API call to prevent 401 errors
            if (_authService.IsTokenExpired(_accessToken))
            {
                Log.Information("Access token is expired or will expire soon. Refreshing...");
                _accessToken = await _tokenRefresher.RefreshAccessToken();
            }
            
            SetAuthHeader(request);
            var response = await _client.ExecuteAsync(request);

            // Only attempt token refresh if we get an actual unauthorized response
            if (response.StatusCode == HttpStatusCode.Unauthorized ||
                (response.Content?.Contains("token is invalid or expired") == true))
            {
                Log.Warning("Received unauthorized response ({StatusCode}). Attempting token refresh...", response.StatusCode);
                Log.Debug("Response content: {Content}", response.Content);
                
                try
                {
                    _accessToken = await _tokenRefresher.RefreshAccessToken();
                    SetAuthHeader(request);
                    response = await _client.ExecuteAsync(request);
                }
                catch (RefreshTokenExpiredException)
                {
                    Log.Error("Refresh token expired during retry. Authentication required.");
                    throw new ReviztoApiException("Authentication required - refresh token expired", HttpStatusCode.Unauthorized);
                }
            }

            if (!response.IsSuccessful)
            {
                Log.Error("API request failed: {Status} - {Error} - Content: {Content}", 
                    response.StatusCode, response.ErrorMessage, response.Content);
                throw new ReviztoApiException($"Status: {response.StatusCode}", response.StatusCode);
            }

            return JObject.Parse(response.Content!);
        }

        private void SetAuthHeader(RestRequest request)
            => request.AddOrUpdateHeader("Authorization", $"Bearer {_accessToken}");

        public class ReviztoApiException : Exception
        {
            public HttpStatusCode StatusCode { get; }
            public ReviztoApiException(string message, HttpStatusCode statusCode) : base(message)
                => StatusCode = statusCode;
        }
    }
}
