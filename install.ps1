# Edward Security Framework — Windows Installer
$ErrorActionPreference = "Stop"
$EdwardDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Installed = @()

Write-Host "Edward Security Framework - Installer" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Detect Claude Code
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if ($claudeCmd) {
    Write-Host "[+] Claude Code detected" -ForegroundColor Green

    $claudePluginsDir = Join-Path $env:USERPROFILE ".claude\plugins"
    New-Item -ItemType Directory -Path $claudePluginsDir -Force | Out-Null

    $target = Join-Path $claudePluginsDir "edward"
    if (Test-Path $target) {
        Remove-Item $target -Recurse -Force -Confirm:$false
    }

    New-Item -ItemType Junction -Path $target -Target $EdwardDir | Out-Null
    Write-Host "    Linked: $target -> $EdwardDir"
    $Installed += "Claude Code"
} else {
    Write-Host "[ ] Claude Code not found (skipping)" -ForegroundColor Gray
}

Write-Host ""

# Detect OpenCode
$opencodeCmd = Get-Command opencode -ErrorAction SilentlyContinue
if ($opencodeCmd) {
    Write-Host "[+] OpenCode detected" -ForegroundColor Green

    $opencodeSkillsDir = Join-Path $env:USERPROFILE ".config\opencode\skills"
    New-Item -ItemType Directory -Path $opencodeSkillsDir -Force | Out-Null

    # Link each skill individually
    Get-ChildItem -Path (Join-Path $EdwardDir "skills") -Directory -Filter "edward-*" | ForEach-Object {
        $skillTarget = Join-Path $opencodeSkillsDir $_.Name
        if (Test-Path $skillTarget) {
            Remove-Item $skillTarget -Recurse -Force -Confirm:$false
        }
        New-Item -ItemType Junction -Path $skillTarget -Target $_.FullName | Out-Null
        Write-Host "    Linked: $skillTarget"
    }

    # Copy commands
    $edwardCmdsDir = Join-Path $EdwardDir ".opencode\commands"
    if (Test-Path $edwardCmdsDir) {
        $opencodeCmdsDir = Join-Path $env:USERPROFILE ".config\opencode\commands"
        New-Item -ItemType Directory -Path $opencodeCmdsDir -Force | Out-Null
        Get-ChildItem -Path $edwardCmdsDir -Filter "*.md" | ForEach-Object {
            Copy-Item $_.FullName -Destination (Join-Path $opencodeCmdsDir $_.Name) -Force
            Write-Host "    Copied: $(Join-Path $opencodeCmdsDir $_.Name)"
        }
    }

    # Copy agents
    $edwardAgentsDir = Join-Path $EdwardDir ".opencode\agents"
    if (Test-Path $edwardAgentsDir) {
        $opencodeAgentsDir = Join-Path $env:USERPROFILE ".config\opencode\agents"
        New-Item -ItemType Directory -Path $opencodeAgentsDir -Force | Out-Null
        Get-ChildItem -Path $edwardAgentsDir -Filter "*.md" | ForEach-Object {
            Copy-Item $_.FullName -Destination (Join-Path $opencodeAgentsDir $_.Name) -Force
            Write-Host "    Copied: $(Join-Path $opencodeAgentsDir $_.Name)"
        }
    }

    $Installed += "OpenCode"
} else {
    Write-Host "[ ] OpenCode not found (skipping)" -ForegroundColor Gray
}

Write-Host ""

if ($Installed.Count -eq 0) {
    Write-Host "No supported agents found." -ForegroundColor Red
    Write-Host "Install Claude Code (https://claude.ai/code) or OpenCode (https://opencode.ai) first."
    exit 1
}

Write-Host "Done! Edward installed for: $($Installed -join ', ')" -ForegroundColor Green
Write-Host ""
Write-Host "Quick start:"
Write-Host "  /edward-code-recon    - Run OWASP Top 10 static analysis"
Write-Host "  /edward-dev           - Quick scan of changed files"
Write-Host "  /edward               - Show pipeline status"
