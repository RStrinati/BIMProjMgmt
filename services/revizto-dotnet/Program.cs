using System;
using System.IO;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Extensions.Configuration;
using Serilog;
using ReviztoDataExporter;

internal static class Program
{
    [STAThread]
    static async Task<int> Main(string[] args)
    {
        bool isConsoleMode = args.Length > 0;
        ConfigureLogging(isConsoleMode);

        try
        {
            Log.Information("Starting Revizto Export Application...");

            // Initialize WinForms rendering settings BEFORE any windows/dialogs are created (GUI mode only)
            if (!isConsoleMode)
            {
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
            }

            // Load configuration
            IConfiguration config = LoadConfiguration();
            string baseUrl = config.GetRequiredSection("ReviztoAPI:BaseUrl").Value ?? throw new Exception("BaseUrl missing.");
            string outputDirectory = config.GetRequiredSection("ExportSettings:OutputDirectory").Value ?? throw new Exception("Output directory missing in appsettings.json");
            string connectionString = config.GetRequiredSection("Database:ConnectionString").Value ?? throw new Exception("Connection string missing.");

            // Ensure authentication
            bool isAuthenticated;
            if (isConsoleMode)
            {
                isAuthenticated = await AuthenticationHelper.EnsureAuthenticatedConsole(baseUrl);
            }
            else
            {
                isAuthenticated = await AuthenticationHelper.EnsureAuthenticated(baseUrl);
            }

            if (!isAuthenticated)
            {
                Log.Error("Authentication failed or cancelled");
                if (isConsoleMode)
                {
                    Console.WriteLine("Authentication failed. Application cannot continue.");
                }
                else
                {
                    MessageBox.Show("Authentication failed. Application cannot continue.", "Authentication Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
                return 1;
            }

            // Load tokens from configuration (they should be fresh after authentication)
            string accessToken = config["ReviztoAPI:AccessToken"] ?? "";
            string refreshToken = config.GetRequiredSection("ReviztoAPI:RefreshToken").Value ?? throw new Exception("RefreshToken missing.");

            // Initialize services
            var apiClient = new ReviztoApiClient(baseUrl, accessToken, refreshToken);
            var licenseService = new UserLicenceService(apiClient, outputDirectory, connectionString);

            // Check if running in command line mode
            if (args.Length > 0)
            {
                // Command line mode
                var cli = new CommandLineInterface(licenseService, connectionString, Log.Logger);
                return await cli.ExecuteAsync(args);
            }
            else
            {
                // GUI mode
                Log.Information("Starting GUI mode...");
                Application.Run(new ExportForm(licenseService, connectionString));
                return 0;
            }
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Fatal error starting the application.");
            return 1;
        }
        finally
        {
            Log.CloseAndFlush();
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


    private static void ConfigureLogging(bool consoleMode = false) =>
        Log.Logger = new LoggerConfiguration()
            .WriteTo.Console(restrictedToMinimumLevel: consoleMode ? Serilog.Events.LogEventLevel.Warning : Serilog.Events.LogEventLevel.Information)
            .WriteTo.File("logs/log.txt", rollingInterval: RollingInterval.Day)
            .CreateLogger();
}
