using System;
using System.IO;
using System.Windows.Forms;
using Microsoft.Extensions.Configuration;
using Serilog;
using ReviztoDataExporter;

internal static class Program
{
    [STAThread]
    static void Main()
    {
        ConfigureLogging();

        try
        {
            Log.Information("Starting Revizto Export UI...");

            // Load configuration
            IConfiguration config = LoadConfiguration();
            string baseUrl = config.GetRequiredSection("ReviztoAPI:BaseUrl").Value ?? throw new Exception("BaseUrl missing.");
            string accessToken = config["ReviztoAPI:AccessToken"] ?? "";
            string refreshToken = config.GetRequiredSection("ReviztoAPI:RefreshToken").Value ?? throw new Exception("RefreshToken missing.");
            string outputDirectory = config.GetRequiredSection("ExportSettings:OutputDirectory").Value ?? throw new Exception("Output directory missing in appsettings.json");
            string connectionString = config.GetRequiredSection("Database:ConnectionString").Value ?? throw new Exception("Connection string missing.");

            // Initialize services
            var apiClient = new ReviztoApiClient(baseUrl, accessToken, refreshToken);

            var licenseService = new UserLicenceService(apiClient, outputDirectory, connectionString);

            // Start WinForms UI
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new ExportForm(licenseService, connectionString));
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Fatal error starting the application.");
        }
        finally
        {
            Log.CloseAndFlush(); // Ensure logs are saved
        }
    }

        private static IConfiguration LoadConfiguration()
        {
            var exePath = AppContext.BaseDirectory;  // ✅ Always points to where the .exe resides
            return new ConfigurationBuilder()
                .SetBasePath(exePath)
                .AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
                .Build();
        }


    private static void ConfigureLogging() =>
        Log.Logger = new LoggerConfiguration()
            .WriteTo.Console()
            .WriteTo.File("logs/log.txt", rollingInterval: RollingInterval.Day)
            .CreateLogger();
}
