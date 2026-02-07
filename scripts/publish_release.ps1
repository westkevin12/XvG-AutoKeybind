# publish_release.ps1
param (
    [Parameter(Mandatory=$true)]
    [string]$Version
)

# Validate Version Format (Optional, basic check)
if ($Version -notmatch "^v\d+\.\d+(\.\d+)?") {
    Write-Warning "Version '$Version' does not look like a standard tag (e.g. v1.0.0). Proceeding anyway..."
}

Write-Host "Preparing to publish release $Version..." -ForegroundColor Cyan

# Define Artifacts
$exePath = "dist\XvGKeybind.exe"
$installerPath = "Output\XvGAutoSetup.exe"
$releaseNotesFile = "RELEASE.md"

# Check if artifacts exist
if (-not (Test-Path $exePath)) {
    Write-Error "Executable not found at $exePath. Did you run build_installer.ps1?"
    exit 1
}
if (-not (Test-Path $installerPath)) {
    Write-Error "Installer not found at $installerPath. Did you run build_installer.ps1?"
    exit 1
}
if (-not (Test-Path $releaseNotesFile)) {
    Write-Error "Release notes file not found at $releaseNotesFile."
    exit 1
}

# Run gh release create
Write-Host "Creating GitHub Release..." -ForegroundColor Cyan
# Using --notes-file to read from RELEASE.md
# Including both the raw EXE and the Installer
gh release create $Version $exePath $installerPath --title "$Version" --notes-file $releaseNotesFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "Release $Version published successfully!" -ForegroundColor Green
} else {
    Write-Host "Failed to create release." -ForegroundColor Red
    exit 1
}
