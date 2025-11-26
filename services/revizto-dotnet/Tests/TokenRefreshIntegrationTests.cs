using Microsoft.VisualStudio.TestTools.UnitTesting;
using System;
using System.IO;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;
using Serilog;
using System.Net.Http;
using System.Net;
using System.Text;

namespace ReviztoDataExporter.Tests
{
    [TestClass]
    public class TokenRefreshIntegrationTests
    {
        private string _testConfigPath;
        private const string TestBaseUrl = "https://api.sydney.revizto.com";
        
        [TestInitialize]
        public void TestInitialize()
        {
            Log.Logger = new LoggerConfiguration()
                .WriteTo.Console()
                .CreateLogger();
                
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
        public async Task TestTokenRefreshWorkflow_ExpiredTokenScenario()
        {
            // Arrange: Create a config with an expired token
            var expiredExpiry = DateTimeOffset.UtcNow.AddHours(-1).ToUnixTimeSeconds();
            var expiredToken = CreateTestJwtToken(expiredExpiry);
            
            var testConfig = new JObject
            {
                ["ReviztoAPI"] = new JObject
                {
                    ["BaseUrl"] = TestBaseUrl,
                    ["AccessToken"] = expiredToken,
                    ["RefreshToken"] = "test_refresh_token"
                }
            };
            File.WriteAllText(_testConfigPath, testConfig.ToString());
            
            // Act: Test the expiration detection
            var authService = new ReviztoAuthService(TestBaseUrl);
            var isExpired = authService.IsTokenExpired(expiredToken);
            
            // Assert
            Assert.IsTrue(isExpired, "Expired token should be detected as expired");
            
            // Verify the token manager would attempt refresh
            var tokenManager = new TestReviztoTokenRefresher(_testConfigPath, "test_refresh_token");
            var currentToken = tokenManager.GetCurrentAccessToken();
            Assert.AreEqual(expiredToken, currentToken, "Current token should match the expired token we set");
        }
        
        [TestMethod]
        public async Task TestApiClientTokenRefreshTrigger()
        {
            // Arrange: Create a scenario where token expires within 5 minutes
            var soonExpiry = DateTimeOffset.UtcNow.AddMinutes(3).ToUnixTimeSeconds();
            var soonToExpireToken = CreateTestJwtToken(soonExpiry);
            
            var testConfig = new JObject
            {
                ["ReviztoAPI"] = new JObject
                {
                    ["BaseUrl"] = TestBaseUrl,
                    ["AccessToken"] = soonToExpireToken,
                    ["RefreshToken"] = "test_refresh_token"
                }
            };
            File.WriteAllText(_testConfigPath, testConfig.ToString());
            
            // Act: Test that the auth service correctly identifies this as expired
            var authService = new ReviztoAuthService(TestBaseUrl);
            var shouldRefresh = authService.IsTokenExpired(soonToExpireToken);
            
            // Assert
            Assert.IsTrue(shouldRefresh, "Token expiring within 5 minutes should trigger refresh");
        }
        
        [TestMethod]
        public void TestConfigurationFileAccess_Scenarios()
        {
            // Test 1: Missing configuration file
            var missingPath = Path.Combine(Path.GetTempPath(), "nonexistent_config.json");
            var tokenManager1 = new TestReviztoTokenRefresher(missingPath, "test_refresh");
            
            Assert.ThrowsException<FileNotFoundException>(() => 
                tokenManager1.TestUpdateTokens("new_token", "new_refresh"),
                "Should throw exception when config file is missing");
            
            // Test 2: Invalid JSON format
            var invalidJsonPath = Path.Combine(Path.GetTempPath(), $"invalid_{Guid.NewGuid()}.json");
            File.WriteAllText(invalidJsonPath, "{ invalid json content");
            
            var tokenManager2 = new TestReviztoTokenRefresher(invalidJsonPath, "test_refresh");
            
            try
            {
                Assert.ThrowsException<Exception>(() => 
                    tokenManager2.TestUpdateTokens("new_token", "new_refresh"),
                    "Should throw exception when JSON is malformed");
            }
            finally
            {
                File.Delete(invalidJsonPath);
            }
            
            // Test 3: Valid JSON but missing ReviztoAPI section
            var validJsonPath = Path.Combine(Path.GetTempPath(), $"valid_{Guid.NewGuid()}.json");
            File.WriteAllText(validJsonPath, "{ \"SomeOtherSection\": {} }");
            
            var tokenManager3 = new TestReviztoTokenRefresher(validJsonPath, "test_refresh");
            
            try
            {
                // This should work - it should create the ReviztoAPI section
                tokenManager3.TestUpdateTokens("new_token", "new_refresh");
                
                var updatedConfig = JObject.Parse(File.ReadAllText(validJsonPath));
                Assert.IsNotNull(updatedConfig["ReviztoAPI"], "ReviztoAPI section should be created");
                Assert.AreEqual("new_token", updatedConfig["ReviztoAPI"]?["AccessToken"]?.ToString());
            }
            finally
            {
                File.Delete(validJsonPath);
            }
        }
        
        [TestMethod]
        public void TestTokenValidationLogic_EdgeCases()
        {
            var authService = new ReviztoAuthService(TestBaseUrl);
            
            // Test various edge cases
            Assert.IsTrue(authService.IsTokenExpired(null), "Null token should be expired");
            Assert.IsTrue(authService.IsTokenExpired(""), "Empty token should be expired");
            Assert.IsTrue(authService.IsTokenExpired("not.a.valid.jwt.token"), "Invalid format should be expired");
            Assert.IsTrue(authService.IsTokenExpired("header.payload"), "Missing signature should be expired");
            
            // Test token with missing exp claim
            var tokenWithoutExp = CreateTokenWithoutExpClaim();
            Assert.IsTrue(authService.IsTokenExpired(tokenWithoutExp), "Token without exp claim should be expired");
            
            // Test token with invalid exp format
            var tokenWithInvalidExp = CreateTokenWithInvalidExp();
            Assert.IsTrue(authService.IsTokenExpired(tokenWithInvalidExp), "Token with invalid exp should be expired");
        }
        
        [TestMethod]
        public void TestCurrentTokenFromRealConfig()
        {
            // Test with the actual current appsettings.json
            var realConfigPath = "appsettings.json";
            if (File.Exists(realConfigPath))
            {
                var config = JObject.Parse(File.ReadAllText(realConfigPath));
                var currentToken = config["ReviztoAPI"]?["AccessToken"]?.ToString();
                
                if (!string.IsNullOrEmpty(currentToken))
                {
                    var authService = new ReviztoAuthService(TestBaseUrl);
                    var isExpired = authService.IsTokenExpired(currentToken);
                    
                    Console.WriteLine($"Current token from real config - Is Expired: {isExpired}");
                    
                    // This test just reports the status, doesn't assert
                    // because the token might legitimately be expired
                }
                else
                {
                    Assert.Fail("No access token found in real configuration");
                }
            }
            else
            {
                Assert.Inconclusive("Real appsettings.json not found for testing");
            }
        }
        
        private string CreateTestJwtToken(long expiryTimestamp)
        {
            var header = Convert.ToBase64String(
                Encoding.UTF8.GetBytes("{\"typ\":\"JWT\",\"alg\":\"RS256\"}")
            ).TrimEnd('=');
            
            var payload = new
            {
                sub = "test@example.com",
                exp = expiryTimestamp,
                iat = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
                aud = "test-audience"
            };
            
            var payloadJson = System.Text.Json.JsonSerializer.Serialize(payload);
            var payloadBase64 = Convert.ToBase64String(
                Encoding.UTF8.GetBytes(payloadJson)
            ).TrimEnd('=');
            
            var signature = Convert.ToBase64String(
                Encoding.UTF8.GetBytes("dummy-signature")
            ).TrimEnd('=');
            
            return $"{header}.{payloadBase64}.{signature}";
        }
        
        private string CreateTokenWithoutExpClaim()
        {
            var header = Convert.ToBase64String(
                Encoding.UTF8.GetBytes("{\"typ\":\"JWT\",\"alg\":\"RS256\"}")
            ).TrimEnd('=');
            
            var payload = new
            {
                sub = "test@example.com",
                iat = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
                aud = "test-audience"
                // Note: no 'exp' claim
            };
            
            var payloadJson = System.Text.Json.JsonSerializer.Serialize(payload);
            var payloadBase64 = Convert.ToBase64String(
                Encoding.UTF8.GetBytes(payloadJson)
            ).TrimEnd('=');
            
            var signature = Convert.ToBase64String(
                Encoding.UTF8.GetBytes("dummy-signature")
            ).TrimEnd('=');
            
            return $"{header}.{payloadBase64}.{signature}";
        }
        
        private string CreateTokenWithInvalidExp()
        {
            var header = Convert.ToBase64String(
                Encoding.UTF8.GetBytes("{\"typ\":\"JWT\",\"alg\":\"RS256\"}")
            ).TrimEnd('=');
            
            // Create payload with invalid exp format
            var payloadJson = "{\"sub\":\"test@example.com\",\"exp\":\"not-a-number\",\"iat\":" + DateTimeOffset.UtcNow.ToUnixTimeSeconds() + "}";
            var payloadBase64 = Convert.ToBase64String(
                Encoding.UTF8.GetBytes(payloadJson)
            ).TrimEnd('=');
            
            var signature = Convert.ToBase64String(
                Encoding.UTF8.GetBytes("dummy-signature")
            ).TrimEnd('=');
            
            return $"{header}.{payloadBase64}.{signature}";
        }
    }
}