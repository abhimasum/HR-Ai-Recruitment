param(
    [string] $ConfirmProjectId
)

$ErrorActionPreference = "Stop"

$ProjectId = "hr-ai-recruitment"
$ExpectedProjectNumber = "278189990066"
$ExpectedAccount = "abhimasum2@gmail.com"
$GitHubRepository = "abhimasum/HR-Ai-Recruitment"
$Region = "us-central1"
$ArtifactRepository = "hr-repo"
$StateBucket = "hr-ai-recruitment-278189990066-tfstate"
$PoolId = "github-hr-pool"
$ProviderId = "hr-recruitment"
$DeployerName = "hr-recruitment-deployer"
$DeployerEmail = "$DeployerName@$ProjectId.iam.gserviceaccount.com"
$GcloudCommand = (Get-Command gcloud.cmd -ErrorAction Stop).Source
$GitHubCommand = (Get-Command gh.exe -ErrorAction Stop).Source

function Invoke-Gcloud {
    param([Parameter(Mandatory = $true)][string[]] $Arguments)
    & $GcloudCommand @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud failed with exit code $LASTEXITCODE"
    }
}

function Invoke-GitHub {
    param([Parameter(Mandatory = $true)][string[]] $Arguments)
    & $GitHubCommand @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "GitHub CLI failed with exit code $LASTEXITCODE"
    }
}

foreach ($tool in @("gcloud.cmd", "gh.exe")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "Install and sign in to '$tool' before running this setup script."
    }
}

$activeAccount = & $GcloudCommand config get-value account 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Could not read the active Google Cloud CLI account."
}
if ([string]::IsNullOrWhiteSpace($activeAccount) -or $activeAccount.Trim() -ne $ExpectedAccount) {
    throw "Sign in to Google Cloud as $ExpectedAccount first: gcloud auth login"
}

$projectNumber = (& $GcloudCommand projects describe $ProjectId --format="value(projectNumber)")
if ($LASTEXITCODE -ne 0 -or $projectNumber.Trim() -ne $ExpectedProjectNumber) {
    throw "Project verification failed. Expected $ProjectId ($ExpectedProjectNumber)."
}

Invoke-GitHub -Arguments @("auth", "status")
Invoke-GitHub -Arguments @("repo", "view", $GitHubRepository, "--json", "nameWithOwner")

Write-Host "Configuring GitHub Actions deployment for $ProjectId ($projectNumber)."
Write-Host "The deployer role grants broad Terraform permissions in this project."
if ([string]::IsNullOrWhiteSpace($ConfirmProjectId)) {
    $confirmation = Read-Host "Type the project ID to continue"
}
else {
    $confirmation = $ConfirmProjectId
}
if ($confirmation -ne $ProjectId) {
    throw "Project confirmation did not match; no resources were changed."
}

Invoke-Gcloud -Arguments @(
    "services", "enable",
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "secretmanager.googleapis.com",
    "--project=$ProjectId"
)

$serviceAccounts = & $GcloudCommand iam service-accounts list --project=$ProjectId --format="value(email)"
if ($LASTEXITCODE -ne 0) {
    throw "Could not list project service accounts."
}
if ($serviceAccounts -notcontains $DeployerEmail) {
    Invoke-Gcloud -Arguments @(
        "iam", "service-accounts", "create", $DeployerName,
        "--project=$ProjectId",
        "--display-name=GitHub Actions HR Recruitment deployer"
    )
}

$projectRoles = @(
    "roles/serviceusage.serviceUsageAdmin",
    "roles/artifactregistry.admin",
    "roles/cloudsql.admin",
    "roles/run.admin",
    "roles/iam.serviceAccountAdmin",
    "roles/resourcemanager.projectIamAdmin",
    "roles/iam.serviceAccountUser",
    "roles/secretmanager.admin"
)
foreach ($role in $projectRoles) {
    Invoke-Gcloud -Arguments @(
        "projects", "add-iam-policy-binding", $ProjectId,
        "--member=serviceAccount:$DeployerEmail",
        "--role=$role",
        "--quiet"
    )
}

$bucketUri = "gs://$StateBucket"
$buckets = & $GcloudCommand storage buckets list --project=$ProjectId --format="value(name)"
if ($LASTEXITCODE -ne 0) {
    throw "Could not list project storage buckets."
}
$bucketNames = @($buckets | ForEach-Object { ($_ -replace "^gs://", "").TrimEnd("/") })
if ($bucketNames -notcontains $StateBucket) {
    Invoke-Gcloud -Arguments @(
        "storage", "buckets", "create", $bucketUri,
        "--project=$ProjectId",
        "--location=$Region",
        "--uniform-bucket-level-access"
    )
}
Invoke-Gcloud -Arguments @("storage", "buckets", "update", $bucketUri, "--versioning")
Invoke-Gcloud -Arguments @(
    "storage", "buckets", "add-iam-policy-binding", $bucketUri,
    "--member=serviceAccount:$DeployerEmail",
    "--role=roles/storage.objectAdmin"
)

$poolEntries = & $GcloudCommand iam workload-identity-pools list `
    --project=$ProjectId --location=global --format=json
if ($LASTEXITCODE -ne 0) {
    throw "Could not list Workload Identity pools."
}
$pools = @($poolEntries | ConvertFrom-Json)
$poolExists = @($pools | Where-Object { $_.name -like "*/workloadIdentityPools/$PoolId" }).Count -gt 0
if (-not $poolExists) {
    Invoke-Gcloud -Arguments @(
        "iam", "workload-identity-pools", "create", $PoolId,
        "--project=$ProjectId",
        "--location=global",
        "--display-name=GitHub Actions HR Recruitment"
    )
}

$attributeCondition = "assertion.repository=='$GitHubRepository' && (assertion.ref=='refs/heads/master' || assertion.ref=='refs/heads/main')"
$providerEntries = & $GcloudCommand iam workload-identity-pools providers list `
    --project=$ProjectId --location=global --workload-identity-pool=$PoolId `
    --format=json
if ($LASTEXITCODE -ne 0) {
    throw "Could not list providers in the Workload Identity pool."
}
$providers = @($providerEntries | ConvertFrom-Json)
$providerExists = @($providers | Where-Object { $_.name -like "*/providers/$ProviderId" }).Count -gt 0
if (-not $providerExists) {
    Invoke-Gcloud -Arguments @(
        "iam", "workload-identity-pools", "providers", "create-oidc", $ProviderId,
        "--project=$ProjectId",
        "--location=global",
        "--workload-identity-pool=$PoolId",
        "--display-name=HR Recruitment GitHub",
        "--issuer-uri=https://token.actions.githubusercontent.com",
        "--attribute-mapping=google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref",
        "--attribute-condition=$attributeCondition"
    )
}
else {
    $providerJson = & $GcloudCommand iam workload-identity-pools providers describe $ProviderId `
        --project=$ProjectId --location=global --workload-identity-pool=$PoolId `
        --format=json
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect the existing Workload Identity provider."
    }
    $providerConfiguration = ($providerJson -join "`n") | ConvertFrom-Json
    $expectedMapping = @{
        "google.subject" = "assertion.sub"
        "attribute.repository" = "assertion.repository"
        "attribute.ref" = "assertion.ref"
    }
    if (
        $providerConfiguration.oidc.issuerUri -ne "https://token.actions.githubusercontent.com" -or
        $providerConfiguration.attributeCondition -ne $attributeCondition -or
        $providerConfiguration.attributeMapping."google.subject" -ne $expectedMapping."google.subject" -or
        $providerConfiguration.attributeMapping."attribute.repository" -ne $expectedMapping."attribute.repository" -or
        $providerConfiguration.attributeMapping."attribute.ref" -ne $expectedMapping."attribute.ref"
    ) {
        throw "The existing WIF provider does not match this repository and branch restriction. Review it before changing it."
    }
}

$providerResource = "projects/$projectNumber/locations/global/workloadIdentityPools/$PoolId/providers/$ProviderId"
$repositoryPrincipal = "principalSet://iam.googleapis.com/projects/$projectNumber/locations/global/workloadIdentityPools/$PoolId/attribute.repository/$GitHubRepository"
Invoke-Gcloud -Arguments @(
    "iam", "service-accounts", "add-iam-policy-binding", $DeployerEmail,
    "--project=$ProjectId",
    "--role=roles/iam.workloadIdentityUser",
    "--member=$repositoryPrincipal"
)

$variables = @{
    GCP_PROJECT_ID = $ProjectId
    GCP_REGION = $Region
    GCP_WORKLOAD_IDENTITY_PROVIDER = $providerResource
    GCP_SERVICE_ACCOUNT = $DeployerEmail
    GCP_TERRAFORM_STATE_BUCKET = $StateBucket
    GCP_ARTIFACT_REGISTRY_REPOSITORY = $ArtifactRepository
}
foreach ($entry in $variables.GetEnumerator()) {
    Invoke-GitHub -Arguments @(
        "variable", "set", $entry.Key,
        "--repo=$GitHubRepository",
        "--body=$($entry.Value)"
    )
}

foreach ($secretName in @("HR_DB_PASSWORD", "HR_DB_ADMIN_PASSWORD")) {
    $randomBytes = New-Object byte[] 32
    $randomGenerator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $randomGenerator.GetBytes($randomBytes)
        $secretValue = ($randomBytes | ForEach-Object { $_.ToString("x2") }) -join ""
    }
    finally {
        $randomGenerator.Dispose()
    }
    Invoke-GitHub -Arguments @(
        "secret", "set", $secretName,
        "--repo=$GitHubRepository",
        "--body=$secretValue"
    )
    $secretValue = $null
    [Array]::Clear($randomBytes, 0, $randomBytes.Length)
}

& (Join-Path $PSScriptRoot "set-initial-accounts.ps1")

Write-Host ""
Write-Host "GitHub Actions WIF, Terraform state, database secrets, and initial account secret are configured."
Write-Host "Repository: https://github.com/$GitHubRepository"
Write-Host "Project: $ProjectId ($projectNumber)"
Write-Host "Region: $Region"
Write-Host "State bucket: $bucketUri"
Write-Host "Run the 'Deploy HR Recruitment App to GCP' workflow from the GitHub Actions tab."
