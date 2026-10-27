$ErrorActionPreference = "Stop"

$GitHubRepository = "abhimasum/HR-Ai-Recruitment"
$GitHubCommand = (Get-Command gh.exe -ErrorAction Stop).Source

& $GitHubCommand auth status
if ($LASTEXITCODE -ne 0) {
    throw "Sign in to GitHub CLI before setting application account passwords."
}

$initialAccounts = @{}
foreach ($username in @("candidate1", "candidate2", "candidate3", "test", "hr")) {
    $securePassword = Read-Host "Enter the initial demo password for $username" -AsSecureString
    if ($securePassword.Length -eq 0) {
        throw "An initial password is required for $username."
    }

    $passwordPointer = [IntPtr]::Zero
    try {
        $passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
        $initialAccounts[$username] = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
    }
    finally {
        if ($passwordPointer -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
        }
        $securePassword.Dispose()
    }
}

$accountJson = $initialAccounts | ConvertTo-Json -Compress
$accountJson | & $GitHubCommand secret set HR_INITIAL_ACCOUNTS_JSON --repo=$GitHubRepository
if ($LASTEXITCODE -ne 0) {
    throw "Could not save the initial application accounts as a GitHub Actions secret."
}
$initialAccounts.Clear()
$accountJson = $null

Write-Host "Initial account bootstrap values saved as a GitHub Actions secret."
