using Microsoft.VisualStudio.TestTools.UnitTesting;
using System;
using System.IO;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;
using Serilog;
using System.Text.Json;

namespace ReviztoDataExporter.Tests
{
    [TestClass]
    public class TokenManagementTests
    {
        private string _testConfigPath;
        private const string TestBaseUrl = "https://api.sydney.revizto.com";
        
        [TestInitialize]
        public void TestInitialize()
        {
            // Set up Serilog for testing
            Log.Logger = new LoggerConfiguration()
                .WriteTo.Console()
                .CreateLogger();
                
            // Create a test config file
            _testConfigPath = Path.Combine(Path.GetTempPath(), $"test_appsettings_{Guid.NewGuid()}.json");
        }
        
        [TestCleanup]
        public void TestCleanup()
        {
            if (File.Exists(_testConfigPath))
            {
                File.Delete(_testConfigPath);
            }
        }
        
        [TestMethod]
        public void TestJwtTokenExpiration_ValidToken()
        {
            // Arrange: Create a JWT token that expires in 1 hour
            var futureExpiry = DateTimeOffset.UtcNow.AddHours(1).ToUnixTimeSeconds();
            var validToken = CreateTestJwtToken(futureExpiry);
            var authService = new ReviztoAuthService(TestBaseUrl);
            
            // Act
            var isExpired = authService.IsTokenExpired(validToken);
            
            // Assert
            Assert.IsFalse(isExpired, "Token should not be expired when it has 1 hour remaining");
        }
        
        [TestMethod]
        public void TestJwtTokenExpiration_ExpiredToken()
        {
            // Arrange: Create a JWT token that expired 1 hour ago
            var pastExpiry = DateTimeOffset.UtcNow.AddHours(-1).ToUnixTimeSeconds();
            var expiredToken = CreateTestJwtToken(pastExpiry);
            var authService = new ReviztoAuthService(TestBaseUrl);
            
            // Act
            var isExpired = authService.IsTokenExpired(expiredToken);
            
            // Assert
            Assert.IsTrue(isExpired, "Token should be expired when it expired 1 hour ago");
        }
        
        [TestMethod]
        public void TestJwtTokenExpiration_ExpiresWithin5Minutes()
        {
            // Arrange: Create a JWT token that expires in 3 minutes
            var soonExpiry = DateTimeOffset.UtcNow.AddMinutes(3).ToUnixTimeSeconds();
            var soonToExpireToken = CreateTestJwtToken(soonExpiry);
            var authService = new ReviztoAuthService(TestBaseUrl);
            
            // Act
            var isExpired = authService.IsTokenExpired(soonToExpireToken);
            
            // Assert
            Assert.IsTrue(isExpired, "Token should be considered expired when it expires within 5 minutes");
        }
        
        [TestMethod]
        public void TestJwtTokenExpiration_DecimalTimestamp()
        {
            // Arrange: Create a JWT token with decimal timestamp (like Revizto uses)
            var futureExpiry = DateTimeOffset.UtcNow.AddHours(1).ToUnixTimeSeconds() + 0.123456;
            var tokenWithDecimal = CreateTestJwtTokenWithDecimal(futureExpiry);
            var authService = new ReviztoAuthService(TestBaseUrl);
            
            // Act
            var isExpired = authService.IsTokenExpired(tokenWithDecimal);
            
            // Assert
            Assert.IsFalse(isExpired, "Token with decimal timestamp should be parsed correctly");
        }
        
        [TestMethod]
        public void TestJwtTokenExpiration_InvalidToken()
        {
            // Arrange
            var authService = new ReviztoAuthService(TestBaseUrl);
            
            // Act & Assert
            Assert.IsTrue(authService.IsTokenExpired(""), "Empty token should be considered expired");
            Assert.IsTrue(authService.IsTokenExpired("invalid.token"), "Invalid token should be considered expired");
            Assert.IsTrue(authService.IsTokenExpired("invalid"), "Malformed token should be considered expired");
        }
        
        [TestMethod]
        public async Task TestConfigurationUpdate_Success()
        {
            // Arrange
            var testConfig = new JObject
            {
                ["ReviztoAPI"] = new JObject
                {
                    ["BaseUrl"] = TestBaseUrl,
                    ["AccessToken"] = "old_token",
                    ["RefreshToken"] = "old_refresh_token"
                }
            };
            File.WriteAllText(_testConfigPath, testConfig.ToString());
            
            // Create a custom token manager that uses our test config path
            var tokenManager = new TestReviztoTokenRefresher(_testConfigPath, "new_refresh_token");
            
            // Act
            tokenManager.TestUpdateTokens("new_access_token", "new_refresh_token");
            
            // Assert
            var updatedConfig = JObject.Parse(File.ReadAllText(_testConfigPath));
            Assert.AreEqual("new_access_token", updatedConfig["ReviztoAPI"]?["AccessToken"]?.ToString());
            Assert.AreEqual("new_refresh_token", updatedConfig["ReviztoAPI"]?["RefreshToken"]?.ToString());
        }
        
        [TestMethod]
        public void TestConfigurationUpdate_ReadOnlyFile()
        {
            // Arrange
            var testConfig = new JObject
            {
                ["ReviztoAPI"] = new JObject
                {
                    ["BaseUrl"] = TestBaseUrl,
                    ["AccessToken"] = "old_token",
                    ["RefreshToken"] = "old_refresh_token"
                }
            };
            File.WriteAllText(_testConfigPath, testConfig.ToString());
            
            // Make file read-only
            File.SetAttributes(_testConfigPath, FileAttributes.ReadOnly);
            
            var tokenManager = new TestReviztoTokenRefresher(_testConfigPath, "refresh_token");
            
            // Act & Assert
            try
            {
                Assert.ThrowsException<Exception>(() => 
                    tokenManager.TestUpdateTokens("new_token", "new_refresh"));
            }
            finally
            {
                // Clean up: remove read-only attribute
                File.SetAttributes(_testConfigPath, FileAttributes.Normal);
            }
        }
        
        [TestMethod]
        public void TestConfigurationUpdate_MissingReviztoAPISection()
        {
            // Arrange
            var testConfig = new JObject
            {
                ["SomeOtherSection"] = new JObject
                {
                    ["Key"] = "Value"
                }
            };
            File.WriteAllText(_testConfigPath, testConfig.ToString());
            
            var tokenManager = new TestReviztoTokenRefresher(_testConfigPath, "refresh_token");
            
            // Act
            tokenManager.TestUpdateTokens("new_access_token", "new_refresh_token");
            
            // Assert
            var updatedConfig = JObject.Parse(File.ReadAllText(_testConfigPath));
            Assert.AreEqual("new_access_token", updatedConfig["ReviztoAPI"]?["AccessToken"]?.ToString());
            Assert.AreEqual("new_refresh_token", updatedConfig["ReviztoAPI"]?["RefreshToken"]?.ToString());
        }
        
        private string CreateTestJwtToken(long expiryTimestamp)
        {
            // Create a simple JWT-like token for testing
            // Header (base64 encoded)
            var header = Convert.ToBase64String(
                System.Text.Encoding.UTF8.GetBytes("{\"typ\":\"JWT\",\"alg\":\"RS256\"}")
            ).TrimEnd('=');
            
            // Payload with expiry
            var payload = new
            {
                sub = "test@example.com",
                exp = expiryTimestamp,
                iat = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
                aud = "test-audience"
            };
            
            var payloadJson = System.Text.Json.JsonSerializer.Serialize(payload);
            var payloadBase64 = Convert.ToBase64String(
                System.Text.Encoding.UTF8.GetBytes(payloadJson)
            ).TrimEnd('=');
            
            // Signature (dummy for testing)
            var signature = Convert.ToBase64String(
                System.Text.Encoding.UTF8.GetBytes("dummy-signature")
            ).TrimEnd('=');
            
            return $"{header}.{payloadBase64}.{signature}";
        }
        
        private string CreateTestJwtTokenWithDecimal(double expiryTimestamp)
        {
            // Create a JWT token with decimal timestamp
            var header = Convert.ToBase64String(
                System.Text.Encoding.UTF8.GetBytes("{\"typ\":\"JWT\",\"alg\":\"RS256\"}")
            ).TrimEnd('=');
            
            // Use manual JSON to ensure decimal format
            var payloadJson = $"{{\"sub\":\"test@example.com\",\"exp\":{expiryTimestamp:F6},\"iat\":{DateTimeOffset.UtcNow.ToUnixTimeSeconds()},\"aud\":\"test-audience\"}}";
            
            var payloadBase64 = Convert.ToBase64String(
                System.Text.Encoding.UTF8.GetBytes(payloadJson)
            ).TrimEnd('=');
            
            var signature = Convert.ToBase64String(
                System.Text.Encoding.UTF8.GetBytes("dummy-signature")
            ).TrimEnd('=');
            
            return $"{header}.{payloadBase64}.{signature}";
        }
    }
    
    // Test helper class to access protected methods
    public class TestReviztoTokenRefresher
    {
        private readonly string _configPath;
        private readonly string _refreshToken;
        
        public TestReviztoTokenRefresher(string configPath, string refreshToken)
        {
            _configPath = configPath;
            _refreshToken = refreshToken;
        }
        
        public void TestUpdateTokens(string accessToken, string refreshToken)
        {
            try
            {
                if (!File.Exists(_configPath))
                {
                    throw new FileNotFoundException($"Configuration file not found: {_configPath}");
                }

                var configJson = JObject.Parse(File.ReadAllText(_configPath));

                if (configJson["ReviztoAPI"] == null)
                {
                    configJson["ReviztoAPI"] = new JObject();
                }

                var reviztoApiSection = configJson["ReviztoAPI"] as JObject;
                if (reviztoApiSection != null)
                {
                    reviztoApiSection["AccessToken"] = accessToken;
                    reviztoApiSection["RefreshToken"] = refreshToken;

                    File.WriteAllText(_configPath, configJson.ToString());
                }
                else
                {
                    throw new Exception("Failed to update tokens: ReviztoAPI section is not a valid JSON object.");
                }
            }
            catch (Exception ex)
            {
                throw new Exception("Error updating tokens in configuration", ex);
            }
        }
        
        public string GetCurrentAccessToken()
        {
            try
            {
                if (!File.Exists(_configPath)) return "";

                var configJson = JObject.Parse(File.ReadAllText(_configPath));
                return configJson["ReviztoAPI"]?["AccessToken"]?.ToString() ?? "";
            }
            catch
            {
                return "";
            }
        }
    }
}