using System;
using System.Threading.Tasks;
using System.Windows.Forms;
using Serilog;

namespace ReviztoDataExporter
{
    public static class AuthenticationHelper
    {
        public static async Task<bool> EnsureAuthenticated(string baseUrl)
        {
            var authService = new ReviztoAuthService(baseUrl);
            
            if (await authService.ValidateCurrentTokens())
            {
                Log.Information("Current tokens are valid");
                return true;
            }

            // Try automatic refresh before prompting for API key
            try
            {
                Log.Information("Attempting automatic token refresh before prompting user...");
                var refresher = new ReviztoTokenRefresher();
                var newAccess = await refresher.RefreshAccessToken();

                // Validate refreshed token
                if (!string.IsNullOrWhiteSpace(newAccess) && await authService.ValidateCurrentTokens())
                {
                    Log.Information("Automatic token refresh succeeded");
                    return true;
                }
            }
            catch (RefreshTokenExpiredException)
            {
                Log.Warning("Refresh token expired. Falling back to API key authentication");
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Automatic token refresh attempt failed");
            }

            Log.Information("Authentication required");
            return await ShowAuthenticationDialog(authService);
        }

        private static async Task<bool> ShowAuthenticationDialog(ReviztoAuthService authService)
        {
            var dialog = new ApiKeyDialog();
            
            if (dialog.ShowDialog() == DialogResult.OK)
            {
                var input = dialog.ApiKey;
                
                if (!string.IsNullOrWhiteSpace(input))
                {
                    try
                    {
                        AuthenticationResult result;
                        var normalized = NormalizeJwtIfPresent(input);
                        // Access Code detection: Revizto example codes are long opaque strings (def502...)
                        var looksLikeAccessCode = normalized.StartsWith("def502", StringComparison.OrdinalIgnoreCase) && !LooksLikeJwt(normalized);
                        var useAccessTokenMode = dialog.IsAccessToken || LooksLikeJwt(normalized);
                        if (looksLikeAccessCode)
                        {
                            result = await authService.AuthenticateWithAccessCode(normalized);
                        }
                        else if (useAccessTokenMode)
                        {
                            // Treat as access token
                            result = await authService.AuthenticateWithAccessToken(normalized);
                        }
                        else
                        {
                            // Treat as API key
                            result = await authService.AuthenticateWithApiKey(input);
                        }
                        
                        if (result.Success)
                        {
                            var mode = result.RefreshToken is null ? "ACCESS TOKEN ONLY" : "FULL TOKENS";
                            MessageBox.Show($"Authentication successful (mode: {mode})!\n\nWelcome, {result.UserInfo?.Name ?? result.UserInfo?.Email}", 
                                "Authentication Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                            return true;
                        }
                        else
                        {
                            MessageBox.Show($"Authentication failed: {result.ErrorMessage}", 
                                "Authentication Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                        }
                    }
                    catch (Exception ex)
                    {
                        Log.Error(ex, "Authentication error");
                        MessageBox.Show($"Authentication error: {ex.Message}", 
                            "Authentication Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }
            }
            
            return false;
        }

        public static async Task<bool> EnsureAuthenticatedConsole(string baseUrl)
        {
            var authService = new ReviztoAuthService(baseUrl);
            
            if (await authService.ValidateCurrentTokens())
            {
                Log.Information("Current tokens are valid");
                return true;
            }

            // Attempt an automatic refresh in console mode too
            try
            {
                Log.Information("Attempting automatic token refresh before prompting for API key (console)...");
                var refresher = new ReviztoTokenRefresher();
                var newAccess = await refresher.RefreshAccessToken();
                if (!string.IsNullOrWhiteSpace(newAccess) && await authService.ValidateCurrentTokens())
                {
                    Log.Information("Automatic token refresh succeeded (console)");
                    return true;
                }
            }
            catch (RefreshTokenExpiredException)
            {
                Log.Warning("Refresh token expired. Console will prompt for API key.");
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Automatic token refresh attempt failed (console)");
            }

            Console.WriteLine("Authentication required.");
            Console.WriteLine("Paste one of: (1) Access Code (def502... from ws.revizto.com), (2) Access Token (JWT), or (3) API Key.");
            Console.WriteLine("- Best practice: Use an Access Code. We'll exchange it for access + refresh tokens.");
            Console.Write("Input: ");
            
            var input = Console.ReadLine();
            
            if (string.IsNullOrWhiteSpace(input))
            {
                Console.WriteLine("No input provided.");
                return false;
            }

            try
            {
                Console.WriteLine("Authenticating...");
                AuthenticationResult result;
                var normalized = NormalizeJwtIfPresent(input);
                var looksLikeAccessCode = normalized.StartsWith("def502", StringComparison.OrdinalIgnoreCase) && !LooksLikeJwt(normalized);
                if (looksLikeAccessCode)
                {
                    result = await authService.AuthenticateWithAccessCode(normalized);
                }
                else if (LooksLikeJwt(normalized))
                {
                    result = await authService.AuthenticateWithAccessToken(normalized);
                }
                else
                {
                    result = await authService.AuthenticateWithApiKey(input);
                }
                
                if (result.Success)
                {
                    var mode = result.RefreshToken is null ? "ACCESS TOKEN ONLY" : "FULL TOKENS";
                    Console.WriteLine($"Authentication successful ({mode})! Welcome, {result.UserInfo?.Name ?? result.UserInfo?.Email}");
                    return true;
                }
                else
                {
                    Console.WriteLine($"Authentication failed: {result.ErrorMessage}");
                    return false;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Authentication error: {ex.Message}");
                Log.Error(ex, "Console authentication error");
                return false;
            }
        }

        private static bool LooksLikeJwt(string input)
        {
            // Quick heuristic: three parts separated by '.' and base64url-friendly chars
            if (string.IsNullOrWhiteSpace(input)) return false;
            var trimmed = input.Trim();
            var parts = trimmed.Split('.');
            if (parts.Length != 3) return false;
            // Basic char check
            foreach (var p in parts)
            {
                foreach (var ch in p)
                {
                    if (!(char.IsLetterOrDigit(ch) || ch == '-' || ch == '_' || ch == '+')) // allow '+' in some enc
                        return false;
                }
            }
            return true;
        }

        private static string NormalizeJwtIfPresent(string input)
        {
            if (string.IsNullOrWhiteSpace(input)) return input ?? "";
            var s = input.Trim();
            if (s.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
            {
                s = s.Substring(7).Trim();
            }
            return s;
        }
    }

    public class ApiKeyDialog : Form
    {
    private TextBox? apiKeyTextBox;
    private CheckBox? accessTokenCheckBox;
        private Button? okButton;
        private Button? cancelButton;

    public string ApiKey { get; private set; } = "";
    public bool IsAccessToken { get; private set; } = false;

        public ApiKeyDialog()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            this.Text = "Revizto Authentication";
            this.Size = new System.Drawing.Size(500, 220);
            this.StartPosition = FormStartPosition.CenterParent;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;

            var label = new Label
            {
                Text = "Paste Revizto Access Code (def502...), Access Token (JWT), or API Key:",
                Location = new System.Drawing.Point(20, 20),
                Size = new System.Drawing.Size(450, 25)
            };

            apiKeyTextBox = new TextBox
            {
                Location = new System.Drawing.Point(20, 50),
                Size = new System.Drawing.Size(450, 25),
                UseSystemPasswordChar = true
            };

            accessTokenCheckBox = new CheckBox
            {
                Text = "This input is an Access Token (JWT)",
                Location = new System.Drawing.Point(20, 80),
                Size = new System.Drawing.Size(250, 25)
            };

            okButton = new Button
            {
                Text = "OK",
                Location = new System.Drawing.Point(315, 120),
                Size = new System.Drawing.Size(75, 30),
                DialogResult = DialogResult.OK
            };
            okButton.Click += OkButton_Click;

            cancelButton = new Button
            {
                Text = "Cancel",
                Location = new System.Drawing.Point(395, 120),
                Size = new System.Drawing.Size(75, 30),
                DialogResult = DialogResult.Cancel
            };

            this.Controls.Add(label);
            this.Controls.Add(apiKeyTextBox);
            this.Controls.Add(accessTokenCheckBox);
            this.Controls.Add(okButton);
            this.Controls.Add(cancelButton);

            this.AcceptButton = okButton;
            this.CancelButton = cancelButton;
        }

        private void OkButton_Click(object? sender, EventArgs e)
        {
            ApiKey = apiKeyTextBox?.Text ?? "";
            // If user checked the box, honor it; otherwise leave false (we also auto-detect in code)
            IsAccessToken = accessTokenCheckBox?.Checked ?? false;
        }
    }
}