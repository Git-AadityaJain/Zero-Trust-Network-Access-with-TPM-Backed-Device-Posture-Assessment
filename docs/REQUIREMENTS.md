# DPA System Requirements

## Python Requirements
See `requirements.txt` for Python package dependencies.

## System Requirements

### Windows
- Windows 10/11 (64-bit)
- TPM 2.0 enabled

### .NET Runtime
- **.NET 6.0 Runtime (x64)** - Required for TPMSigner.exe
  - Download: https://dotnet.microsoft.com/download/dotnet/6.0/runtime
  - Or install via winget: `winget install Microsoft.DotNet.Runtime.6`

### Python
- Python 3.8+ (64-bit)

## Installation

### 1. Install .NET Runtime
winget install Microsoft.DotNet.Runtime.6



### 2. Install Python Dependencies
pip install -r requirements.txt



### 3. Verify TPMSigner
.\TPMSigner.exe status

undefined