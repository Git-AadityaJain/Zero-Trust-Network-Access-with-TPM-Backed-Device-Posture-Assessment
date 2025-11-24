using System;
using System.Security.Cryptography;
using System.Text;

namespace TPMSigner
{
    class Program
    {
        private const string KEY_CONTAINER_NAME = "DPA_TPM_Key";

        static void Main(string[] args)
        {
            try
            {
                if (args.Length == 0)
                {
                    ShowUsage();
                    Environment.Exit(1);
                }

                string command = args[0].ToLower();

                switch (command)
                {
                    case "init-key":
                        InitKey();
                        break;
                    case "status":
                        CheckStatus();
                        break;
                    case "sign":
                        if (args.Length < 2)
                        {
                            Console.Error.WriteLine("Error: 'sign' command requires data argument");
                            Environment.Exit(1);
                        }
                        SignData(args[1]);
                        break;
                    default:
                        Console.Error.WriteLine($"Error: Unknown command '{command}'");
                        ShowUsage();
                        Environment.Exit(1);
                        break;
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Error: {ex.Message}");
                Environment.Exit(1);
            }
        }

        static void ShowUsage()
        {
            Console.WriteLine("TPM Signer - Hardware-bound cryptographic operations");
            Console.WriteLine("\nUsage:");
            Console.WriteLine("  TPMSigner.exe init-key              - Initialize TPM key");
            Console.WriteLine("  TPMSigner.exe status                - Check TPM status");
            Console.WriteLine("  TPMSigner.exe sign <base64-data>    - Sign data");
        }

        static void InitKey()
        {
            try
            {
                var cspParams = new CspParameters
                {
                    KeyContainerName = KEY_CONTAINER_NAME,
                    Flags = CspProviderFlags.UseMachineKeyStore
                };

                using (var rsa = new RSACryptoServiceProvider(2048, cspParams))
                {
                    rsa.PersistKeyInCsp = true;
                    byte[] publicKeyBytes = rsa.ExportSubjectPublicKeyInfo();
                    string publicKeyBase64 = Convert.ToBase64String(publicKeyBytes);

                    Console.WriteLine("[OUTPUT_START]");
                    Console.WriteLine(publicKeyBase64);
                    Console.WriteLine("[OUTPUT_END]");
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"TPM key initialization failed: {ex.Message}");
                Environment.Exit(1);
            }
        }

        static void CheckStatus()
        {
            try
            {
                bool tpmAvailable = true;
                bool keyExists = false;

                var cspParams = new CspParameters
                {
                    KeyContainerName = KEY_CONTAINER_NAME,
                    Flags = CspProviderFlags.UseMachineKeyStore
                };

                try
                {
                    using (var rsa = new RSACryptoServiceProvider(cspParams))
                    {
                        keyExists = rsa.CspKeyContainerInfo.Accessible;
                    }
                }
                catch
                {
                    keyExists = false;
                }

                string statusJson = $"{{\"tpm_available\": {tpmAvailable.ToString().ToLower()}, " +
                                  $"\"key_exists\": {keyExists.ToString().ToLower()}}}";

                Console.WriteLine("[OUTPUT_START]");
                Console.WriteLine(statusJson);
                Console.WriteLine("[OUTPUT_END]");

                Environment.Exit(keyExists ? 0 : 2);
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Status check failed: {ex.Message}");
                Environment.Exit(1);
            }
        }

        static void SignData(string base64Data)
        {
            try
            {
                var cspParams = new CspParameters
                {
                    KeyContainerName = KEY_CONTAINER_NAME,
                    Flags = CspProviderFlags.UseMachineKeyStore
                };

                using (var rsa = new RSACryptoServiceProvider(cspParams))
                {
                    byte[] dataToSign = Convert.FromBase64String(base64Data);
                    byte[] signature = rsa.SignData(dataToSign, SHA256.Create());
                    string signatureBase64 = Convert.ToBase64String(signature);

                    Console.WriteLine("[OUTPUT_START]");
                    Console.WriteLine(signatureBase64);
                    Console.WriteLine("[OUTPUT_END]");
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Signing failed: {ex.Message}");
                Environment.Exit(1);
            }
        }
    }
}
