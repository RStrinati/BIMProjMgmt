using System;
using System.Diagnostics;
using System.Net.Http;
using System.Threading.Tasks;
using Serilog;
using Newtonsoft.Json.Linq;
using ReviztoDataExporter;


public static class ApiCallHelper
{
    private const int MaxRetries = 3;
    private const int RetryDelayMs = 1000; // 1 second between retries

    public static async Task<JObject?> SafeApiCall(Func<Task<JObject>> apiCall, string operationName)
    {
        int attempt = 0;
        Stopwatch stopwatch = Stopwatch.StartNew();

        while (attempt < MaxRetries)
        {
            try
            {
                Log.Information($"Starting operation: {operationName} (Attempt {attempt + 1}/{MaxRetries})");

                var result = await apiCall();
                
                // Check if API response contains an error field
                if (result["error"] != null)
                {
                    Log.Warning($"API returned an error for {operationName}: {result["error"]}");
                    return null;
                }

                Log.Information($"Operation successful: {operationName} (Duration: {stopwatch.ElapsedMilliseconds} ms)");
                return result;
            }
            catch (HttpRequestException httpEx)
            {
                if (httpEx.StatusCode == System.Net.HttpStatusCode.Unauthorized || 
                    httpEx.StatusCode == System.Net.HttpStatusCode.Forbidden)
                {
                    Log.Error(httpEx, $"Fatal error ({httpEx.StatusCode}) during {operationName}. Aborting retries.");
                    return null;
                }

                Log.Warning(httpEx, $"Network error during {operationName}. Retrying in {RetryDelayMs} ms...");
            }
            catch (Exception ex)
            {
                Log.Warning(ex, $"Error during {operationName}. Retrying in {RetryDelayMs} ms...");
            }

            await Task.Delay(RetryDelayMs);
            attempt++;
        }

        Log.Error($"Operation failed after {MaxRetries} attempts: {operationName}");
        return null;
    }
}
