using System;
using System.IO;
using System.Security.Cryptography;

class KeyGenerator
{
    static void Main(string[] args)
    {
        // Retrieve the encryption key and IV from environment variables
        string key = Environment.GetEnvironmentVariable("ENCRYPTION_KEY");
        string iv = Environment.GetEnvironmentVariable("ENCRYPTION_IV");

        if (string.IsNullOrEmpty(key) || string.IsNullOrEmpty(iv))
        {
            Console.WriteLine("ERROR: Encryption key or IV is not set in the environment variables.");
            return;
        }

        // Plaintext tokens to encrypt
        string accessToken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIzMjgzODRhYTg1M2E2YTJjYWNmMTQzZGRjNmY4MTkyZSIsImp0aSI6IjJmYmUzMjkxMDkwYWQ2N2Y5MTIyMzVkODk0MTRkNDNjOGM1MDNiYTEzMzVhOTAwMzRkMjUzOGI0YmMzODM4ZDYyMmQ1NGQ5NWZiOWI3YzBjIiwiaWF0IjoxNzMyMjI5NTg2LjMwNTg5MSwiaXNzIjoie1wiaG9zdFwiOlwiYXBpLnN5ZG5leS5yZXZpenRvLmNvbVwiLFwicG9ydFwiOjQ0MyxcInByb3RvY29sXCI6XCJodHRwc1wiLFwidGltZXpvbmVfbmFtZVwiOlwiQUNTVFwiLFwidGltZXpvbmVfc2hpZnRcIjpcIkF1c3RyYWxpYVxcL0RhcndpblwifSIsIm5iZiI6MTczMjIyOTU4Ni4zMDU4OTM5LCJleHAiOjE3MzIyMzMxODYuMjYzODE2MSwic3ViIjoicmljby5zdHJpbmF0aUBpaW1iZS5pbyIsInNjb3BlcyI6WyJvcGVuQXBpIl19.D2Dul56PH7fjei-3p-Wtxcf1bA55Bx0twNOdIfF93dDGxhKg20pecj5yyl5ApVY4ZodahUxlYVMLidkiaZ_0WQTiYcLjSfLW7lbvnQYUrdtWB9F1_zl6_9ukxz-_EGN7684Ljl7h0YhY9yvEikYCGxWWuoHlvLB2-dK2aXyadL-5Ndb4pqKCnUfldgqE2Mw8QSBHNLGDlO0ea-g79TPBp5nVfDJyb-vCQH_l_zLy2n0-Hh2hKSnS4Qg5-UBbEy68Z53igYtZ4AemYr1u4nmd6p5yVkefw-YNbK8zg9nomJL7WIwUGLYrADprVRnbdxJM_CFw2hF1XtNIqGC2qupcCw";
        string refreshToken = "def502003d6a1f6a3e4bdc02637289785681d9c1a14270d87d173c7405c5221c4fac9d4a2a4c22f4b4bc13988d43adafbf3de970bb24e6c4b1b6be0c7aae1f6d539d77bc8c103b7035d8078fe69e92a2a74b083f40f6eb522962ef703ec6fcfc3bf5ef5959be9ad71d38455f8fa238cc0b58dfcf47c73c183d61e13bf2635d43ca62cd1b497b436d9bf8ffff9ec1ee7835629956889d8e76536d2ba8707b7740d78f118d39130e71066b60a2eea4f27512ff31e65a05bf49b4d18315bd21165230a29f41aba8bd67e7f96f9d0dfa55805b0742a7d264d3e46a47f85052b0e273fdd1f1c3d3122edfa04ccd1a4a88abf2cb5c4023feaca40c748844fdcff875ae22bb25590668d897d02379b58a4f8c0403a838c643be969817d7740653350f08f6a4ca9edd6da5f7a47bbccf1d36e8aee16f0878800f2082554cf53a0b4d03779ecd138e3a516db8cf5067b981ad99b41d7dda02516f3a97e5e899f35053127408071a39abadd96c36ec21cb01a1bdb5d7e62bc55e7a60d0626cc22cf86a775d368deec276a2e8fae42747f969ee4f2e109ffa79a1246ea9fa578baaf5e6298e2fdfe3ce822f1ebd89b8d762ae7cdca00a6a875391d3f0cda44b8546e8c4133d59aaf0cfc19b33a60dc1a88274934b161a39350caa7a9c2dddebb4c36a51be27657ad9bdd5bfbb8325b492198403e315e33acbd7e3d2810e2b55f616ec97ed8e612dff8e2983ea841826ad1b0d019af1d49e2361f0e349724e308fe143fd16cbe6bad8dfb67296c52a87b75839fa5993a4879553fcca3b59092913327d248e48a7cbe6d58b38b056011e9c1cc75ed4facbe2f87cb868a134deaafda061880f7923196588";

        // Encrypt the tokens using the EncryptionHelper method
        string encryptedAccessToken = EncryptionHelper.Encrypt(accessToken, key, iv);
        string encryptedRefreshToken = EncryptionHelper.Encrypt(refreshToken, key, iv);

        // Print the encrypted tokens
        Console.WriteLine("Encrypted AccessToken: " + encryptedAccessToken);
        Console.WriteLine("Encrypted RefreshToken: " + encryptedRefreshToken);
    }
}

public static class EncryptionHelper
{
    public static string Encrypt(string plainText, string key, string iv)
    {
        using (var aes = Aes.Create())
        {
            aes.Key = Convert.FromBase64String(key);
            aes.IV = Convert.FromBase64String(iv);
            aes.Padding = PaddingMode.PKCS7;

            using (var encryptor = aes.CreateEncryptor(aes.Key, aes.IV))
            using (var ms = new MemoryStream())
            {
                using (var cs = new CryptoStream(ms, encryptor, CryptoStreamMode.Write))
                using (var sw = new StreamWriter(cs))
                {
                    sw.Write(plainText);
                }
                return Convert.ToBase64String(ms.ToArray());
            }
        }
    }
}
