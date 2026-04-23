# Zentra Security Skills — Windows Installer
$ErrorActionPreference = "Stop"
$ZentraDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host " ______  ______   ___   __    _________  ______    ________     " -ForegroundColor Cyan
Write-Host "/_____/\/_____/\ /__/\ /__/\ /________/\/_____/\  /_______/\    " -ForegroundColor Cyan
Write-Host "\:::__\/\::::_\/_\::\_\\  \ \\__.::.__\/\:::_ \ \ \::: _  \ \   " -ForegroundColor Cyan
Write-Host "   /: /  \:\/___/\\:. ``-\  \ \  \::\ \   \:(_) ) )_\::(_)  \ \  " -ForegroundColor Cyan
Write-Host "  /::/___ \::___\/_\:. _    \ \  \::\ \   \: __ ``\ \\:: __  \ \ " -ForegroundColor Cyan
Write-Host " /_:/____/\\:\____/\\. ``-\  \ \  \::\ \   \ \ ``\ \ \\:.\ \  \ \" -ForegroundColor Cyan
Write-Host " \_______\/ \_____\/ \__\/ \__\/   \__\/    \_\/ \_\/ \__\/\__\/" -ForegroundColor Cyan
Write-Host "                                                                " -ForegroundColor Cyan
Write-Host "            Zentra Security Skills - Installer               " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# --- Progress bar ---
function Show-Progress {
    param([int]$Current, [int]$Total)
    $width = 40
    $pct = [math]::Floor($Current * 100 / $Total)
    $filled = [math]::Floor($Current * $width / $Total)
    $empty = $width - $filled
    $bar = ("#" * $filled) + ("." * $empty)
    Write-Host "`r  [$bar] $($pct.ToString().PadLeft(3))%" -NoNewline
}

# --- Detection phase ---
$hasClaude = $null -ne (Get-Command claude -ErrorAction SilentlyContinue)
$hasOpenCode = $null -ne (Get-Command opencode -ErrorAction SilentlyContinue)

$claudeExists = $false
$opencodeExists = $false

if ($hasClaude) {
    $claudeTarget = Join-Path $env:USERPROFILE ".claude\plugins\zentra"
    if (Test-Path $claudeTarget) { $claudeExists = $true }
}

if ($hasOpenCode) {
    $opencodeSkillCheck = Join-Path $env:USERPROFILE ".config\opencode\skills\zentra-code-recon"
    if (Test-Path $opencodeSkillCheck) { $opencodeExists = $true }
}

# --- Show detected agents ---
Write-Host "Detected agents:" -ForegroundColor White
Write-Host ""

if ($hasClaude) {
    if ($claudeExists) {
        Write-Host "  [+] Claude Code  (Zentra already installed - will update)" -ForegroundColor Green
    } else {
        Write-Host "  [+] Claude Code  (fresh install)" -ForegroundColor Green
    }
} else {
    Write-Host "  [ ] Claude Code  (not found)" -ForegroundColor Gray
}

if ($hasOpenCode) {
    if ($opencodeExists) {
        Write-Host "  [+] OpenCode     (Zentra already installed - will update)" -ForegroundColor Green
    } else {
        Write-Host "  [+] OpenCode     (fresh install)" -ForegroundColor Green
    }
} else {
    Write-Host "  [ ] OpenCode     (not found)" -ForegroundColor Gray
}

Write-Host ""

# --- No agents found ---
if (-not $hasClaude -and -not $hasOpenCode) {
    Write-Host "No supported agents found." -ForegroundColor Red
    Write-Host "Install Claude Code (https://claude.ai/code) or OpenCode (https://opencode.ai) first."
    exit 1
}

# --- Build menu ---
Write-Host "Where would you like to install Zentra?" -ForegroundColor White
Write-Host ""

$options = @()
if ($hasClaude -and $hasOpenCode) {
    $options = @("Claude Code", "OpenCode", "Both", "Cancel")
    Write-Host "  1) Claude Code"
    Write-Host "  2) OpenCode"
    Write-Host "  3) Both"
    Write-Host "  4) Cancel"
} elseif ($hasClaude) {
    $options = @("Claude Code", "Cancel")
    Write-Host "  1) Claude Code"
    Write-Host "  2) Cancel"
} elseif ($hasOpenCode) {
    $options = @("OpenCode", "Cancel")
    Write-Host "  1) OpenCode"
    Write-Host "  2) Cancel"
}

Write-Host ""
$choice = Read-Host "Select [1-$($options.Count)]"

$choiceNum = 0
if (-not [int]::TryParse($choice, [ref]$choiceNum) -or $choiceNum -lt 1 -or $choiceNum -gt $options.Count) {
    Write-Host "Invalid selection. Exiting." -ForegroundColor Red
    exit 1
}

$selected = $options[$choiceNum - 1]

if ($selected -eq "Cancel") {
    Write-Host "Installation cancelled."
    exit 0
}

$installClaude = ($selected -eq "Claude Code") -or ($selected -eq "Both")
$installOpenCode = ($selected -eq "OpenCode") -or ($selected -eq "Both")

Write-Host ""

# --- Count total steps ---
$totalSteps = 0
$currentStep = 0

if ($installClaude) { $totalSteps++ }

if ($installOpenCode) {
    $totalSteps += (Get-ChildItem -Path (Join-Path $ZentraDir "skills") -Directory -Filter "zentra-*").Count
    $cmdsDir = Join-Path $ZentraDir ".opencode\commands"
    if (Test-Path $cmdsDir) {
        $totalSteps += (Get-ChildItem -Path $cmdsDir -Filter "*.md").Count
    }
    $agentsDir = Join-Path $ZentraDir ".opencode\agents"
    if (Test-Path $agentsDir) {
        $totalSteps += (Get-ChildItem -Path $agentsDir -Filter "*.md").Count
    }
}

# --- Silent install functions ---
function Install-Claude {
    $claudePluginsDir = Join-Path $env:USERPROFILE ".claude\plugins"
    New-Item -ItemType Directory -Path $claudePluginsDir -Force | Out-Null

    $target = Join-Path $claudePluginsDir "zentra"
    if (Test-Path $target) {
        Remove-Item $target -Recurse -Force -Confirm:$false
    }

    New-Item -ItemType Junction -Path $target -Target $ZentraDir | Out-Null
    $script:currentStep++
    Show-Progress -Current $script:currentStep -Total $totalSteps
}

function Install-OpenCode {
    $opencodeSkillsDir = Join-Path $env:USERPROFILE ".config\opencode\skills"
    New-Item -ItemType Directory -Path $opencodeSkillsDir -Force | Out-Null

    Get-ChildItem -Path (Join-Path $ZentraDir "skills") -Directory -Filter "zentra-*" | ForEach-Object {
        $skillTarget = Join-Path $opencodeSkillsDir $_.Name
        if (Test-Path $skillTarget) {
            Remove-Item $skillTarget -Recurse -Force -Confirm:$false
        }
        New-Item -ItemType Junction -Path $skillTarget -Target $_.FullName | Out-Null
        $script:currentStep++
        Show-Progress -Current $script:currentStep -Total $totalSteps
    }

    $zentraCmdsDir = Join-Path $ZentraDir ".opencode\commands"
    if (Test-Path $zentraCmdsDir) {
        $opencodeCmdsDir = Join-Path $env:USERPROFILE ".config\opencode\commands"
        New-Item -ItemType Directory -Path $opencodeCmdsDir -Force | Out-Null
        Get-ChildItem -Path $zentraCmdsDir -Filter "*.md" | ForEach-Object {
            Copy-Item $_.FullName -Destination (Join-Path $opencodeCmdsDir $_.Name) -Force
            $script:currentStep++
            Show-Progress -Current $script:currentStep -Total $totalSteps
        }
    }

    $zentraAgentsDir = Join-Path $ZentraDir ".opencode\agents"
    if (Test-Path $zentraAgentsDir) {
        $opencodeAgentsDir = Join-Path $env:USERPROFILE ".config\opencode\agents"
        New-Item -ItemType Directory -Path $opencodeAgentsDir -Force | Out-Null
        Get-ChildItem -Path $zentraAgentsDir -Filter "*.md" | ForEach-Object {
            Copy-Item $_.FullName -Destination (Join-Path $opencodeAgentsDir $_.Name) -Force
            $script:currentStep++
            Show-Progress -Current $script:currentStep -Total $totalSteps
        }
    }
}

# --- Execute ---
$action = "Installing"
if (($installClaude -and $claudeExists) -or ($installOpenCode -and $opencodeExists)) {
    $action = "Updating"
}
Write-Host "$action Zentra..." -ForegroundColor Yellow
Write-Host ""

if ($installClaude) {
    Install-Claude
}

if ($installOpenCode) {
    Install-OpenCode
}

Write-Host ""
Write-Host ""

Start-Sleep -Seconds 2

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Thank you for installing Zentra! -rafael@kodecraft.dev" -ForegroundColor Green
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quick start:"
Write-Host "  /zentra-code-recon    - Run OWASP Top 10 static analysis"
Write-Host "  /zentra-dev           - Quick scan of changed files"
Write-Host "  /zentra               - Show pipeline status"
