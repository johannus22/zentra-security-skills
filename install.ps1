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

$hasCursor = Test-Path (Join-Path $env:USERPROFILE ".cursor")
$cursorExists = $false

if ($hasCursor) {
    $cursorRulesDir = Join-Path $env:USERPROFILE ".cursor\rules"
    if ((Test-Path $cursorRulesDir) -and (Get-ChildItem -Path $cursorRulesDir -Filter "zentra-*.mdc" -ErrorAction SilentlyContinue).Count -gt 0) {
        $cursorExists = $true
    }
}

$hasCodex = ($null -ne (Get-Command codex -ErrorAction SilentlyContinue)) -or (Test-Path (Join-Path $env:USERPROFILE ".codex"))
$codexExists = $false

if ($hasCodex) {
    $codexSkillCheck = Join-Path $env:USERPROFILE ".codex\skills\zentra-code-recon"
    $codexPluginCheck = Join-Path $env:USERPROFILE "plugins\zentra"
    $codexLegacyCheck = Join-Path $env:USERPROFILE ".codex\zentra"
    if ((Test-Path $codexSkillCheck) -or (Test-Path $codexPluginCheck) -or ((Test-Path $codexLegacyCheck) -and (Get-ChildItem -Path $codexLegacyCheck -Filter "zentra-*.md" -ErrorAction SilentlyContinue).Count -gt 0)) {
        $codexExists = $true
    }
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

if ($hasCursor) {
    if ($cursorExists) {
        Write-Host "  [+] Cursor IDE   (Zentra already installed - will update)" -ForegroundColor Green
    } else {
        Write-Host "  [+] Cursor IDE   (fresh install)" -ForegroundColor Green
    }
} else {
    Write-Host "  [ ] Cursor IDE   (not found)" -ForegroundColor Gray
}

if ($hasCodex) {
    if ($codexExists) {
        Write-Host "  [+] Codex CLI    (Zentra already installed - will update)" -ForegroundColor Green
    } else {
        Write-Host "  [+] Codex CLI    (fresh install)" -ForegroundColor Green
    }
} else {
    Write-Host "  [ ] Codex CLI    (not found)" -ForegroundColor Gray
}

Write-Host ""

# --- No agents found ---
if (-not $hasClaude -and -not $hasOpenCode -and -not $hasCursor -and -not $hasCodex) {
    Write-Host "No supported agents found." -ForegroundColor Red
    Write-Host "Install Claude Code (https://claude.ai/code), OpenCode (https://opencode.ai), Cursor IDE, or Codex CLI first."
    exit 1
}

# --- Build menu ---
Write-Host "Where would you like to install Zentra?" -ForegroundColor White
Write-Host ""

$options = @()
if ($hasClaude)   { $options += "Claude Code" }
if ($hasOpenCode) { $options += "OpenCode" }
if ($hasCursor)   { $options += "Cursor IDE" }
if ($hasCodex)    { $options += "Codex CLI" }

$platformCount = @($hasClaude, $hasOpenCode, $hasCursor, $hasCodex) | Where-Object { $_ } | Measure-Object | Select-Object -ExpandProperty Count
if ($platformCount -gt 1) { $options += "All" }
$options += "Cancel"

for ($i = 0; $i -lt $options.Count; $i++) {
    Write-Host "  $($i + 1)) $($options[$i])"
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

$installClaude   = ($selected -eq "Claude Code") -or ($selected -eq "All" -and $hasClaude)
$installOpenCode = ($selected -eq "OpenCode")    -or ($selected -eq "All" -and $hasOpenCode)
$installCursor   = ($selected -eq "Cursor IDE")  -or ($selected -eq "All" -and $hasCursor)
$installCodex    = ($selected -eq "Codex CLI")   -or ($selected -eq "All" -and $hasCodex)

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

if ($installCursor) {
    $cursorMdcDir = Join-Path $ZentraDir ".cursor\rules"
    if (Test-Path $cursorMdcDir) {
        $totalSteps += (Get-ChildItem -Path $cursorMdcDir -Filter "zentra-*.mdc").Count
    }
}

if ($installCodex) {
    $codexNativeSkillDir = Join-Path $ZentraDir "skills"
    $codexLegacySkillDir = Join-Path $ZentraDir ".codex"
    if (Test-Path $codexNativeSkillDir) {
        $totalSteps += (Get-ChildItem -Path $codexNativeSkillDir -Directory -Filter "zentra-*").Count
    }
    if (Test-Path $codexLegacySkillDir) {
        $totalSteps += (Get-ChildItem -Path $codexLegacySkillDir -Filter "zentra-*.md").Count
    }
    $totalSteps += 3
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

function Install-Cursor {
    $cursorRulesDir = Join-Path $env:USERPROFILE ".cursor\rules"
    New-Item -ItemType Directory -Path $cursorRulesDir -Force | Out-Null

    $zentraMdcDir = Join-Path $ZentraDir ".cursor\rules"
    if (Test-Path $zentraMdcDir) {
        Get-ChildItem -Path $zentraMdcDir -Filter "zentra-*.mdc" | ForEach-Object {
            Copy-Item $_.FullName -Destination (Join-Path $cursorRulesDir $_.Name) -Force
            $script:currentStep++
            Show-Progress -Current $script:currentStep -Total $totalSteps
        }
        # Flat rules carry adjacent validator/reference resources.
        Get-ChildItem -LiteralPath $zentraMdcDir -Directory -Filter "zentra-*" | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $cursorRulesDir -Recurse -Force
        }
    }
}

function Install-Codex {
    $codexSkillsDir = Join-Path $env:USERPROFILE ".codex\skills"
    New-Item -ItemType Directory -Path $codexSkillsDir -Force | Out-Null

    Get-ChildItem -Path (Join-Path $ZentraDir "skills") -Directory -Filter "zentra-*" | ForEach-Object {
        $skillTarget = Join-Path $codexSkillsDir $_.Name
        if (Test-Path $skillTarget) {
            Remove-Item $skillTarget -Recurse -Force -Confirm:$false
        }
        New-Item -ItemType Junction -Path $skillTarget -Target $_.FullName | Out-Null
        $script:currentStep++
        Show-Progress -Current $script:currentStep -Total $totalSteps
    }

    $pluginsDir = Join-Path $env:USERPROFILE "plugins"
    New-Item -ItemType Directory -Path $pluginsDir -Force | Out-Null
    $pluginTarget = Join-Path $pluginsDir "zentra"
    if (Test-Path $pluginTarget) {
        Remove-Item $pluginTarget -Recurse -Force -Confirm:$false
    }
    New-Item -ItemType Junction -Path $pluginTarget -Target $ZentraDir | Out-Null
    $script:currentStep++
    Show-Progress -Current $script:currentStep -Total $totalSteps

    $agentsPluginsDir = Join-Path $env:USERPROFILE ".agents\plugins"
    New-Item -ItemType Directory -Path $agentsPluginsDir -Force | Out-Null
    $marketplacePath = Join-Path $agentsPluginsDir "marketplace.json"
    if (Test-Path $marketplacePath) {
        $marketplace = Get-Content $marketplacePath -Raw | ConvertFrom-Json
    } else {
        $marketplace = [pscustomobject]@{
            name = "local-marketplace"
            interface = [pscustomobject]@{
                displayName = "Local Plugins"
            }
            plugins = @()
        }
    }

    if (-not $marketplace.PSObject.Properties.Match("name")) {
        $marketplace | Add-Member -NotePropertyName name -NotePropertyValue "local-marketplace"
    }
    if (-not $marketplace.PSObject.Properties.Match("interface") -or $null -eq $marketplace.interface) {
        $marketplace | Add-Member -NotePropertyName interface -NotePropertyValue ([pscustomobject]@{
            displayName = "Local Plugins"
        }) -Force
    } elseif (-not $marketplace.interface.PSObject.Properties.Match("displayName")) {
        $marketplace.interface | Add-Member -NotePropertyName displayName -NotePropertyValue "Local Plugins"
    }
    if (-not $marketplace.PSObject.Properties.Match("plugins") -or $null -eq $marketplace.plugins) {
        $marketplace | Add-Member -NotePropertyName plugins -NotePropertyValue @() -Force
    }

    $existingPlugins = @($marketplace.plugins | Where-Object { $_.name -ne "zentra" })
    $existingPlugins += [pscustomobject]@{
        name = "zentra"
        source = [pscustomobject]@{
            source = "local"
            path = "./plugins/zentra"
        }
        policy = [pscustomobject]@{
            installation = "AVAILABLE"
            authentication = "ON_INSTALL"
        }
        category = "Security"
    }
    $marketplace.plugins = $existingPlugins
    $marketplace | ConvertTo-Json -Depth 8 | Set-Content -Path $marketplacePath -Encoding utf8
    $script:currentStep++
    Show-Progress -Current $script:currentStep -Total $totalSteps

    $codexZentraDir = Join-Path $env:USERPROFILE ".codex\zentra"
    New-Item -ItemType Directory -Path $codexZentraDir -Force | Out-Null

    $zentraCodexDir = Join-Path $ZentraDir ".codex"
    if (Test-Path $zentraCodexDir) {
        Get-ChildItem -Path $zentraCodexDir -Filter "zentra-*.md" | ForEach-Object {
            Copy-Item $_.FullName -Destination (Join-Path $codexZentraDir $_.Name) -Force
            $script:currentStep++
            Show-Progress -Current $script:currentStep -Total $totalSteps
        }
        Get-ChildItem -LiteralPath $zentraCodexDir -Directory -Filter "zentra-*" | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $codexZentraDir -Recurse -Force
        }
    }

    $codexAgents   = Join-Path $env:USERPROFILE ".codex\AGENTS.md"
    $markerStart   = "<!-- zentra:start -->"
    $markerEnd     = "<!-- zentra:end -->"
    $zentraSection = Get-Content (Join-Path $ZentraDir ".codex\AGENTS.md") -Raw

    if (-not (Test-Path $codexAgents)) {
        Set-Content -Path $codexAgents -Value "$markerStart`n$zentraSection`n$markerEnd" -Encoding utf8
    } elseif ((Get-Content $codexAgents -Raw) -match [regex]::Escape($markerStart)) {
        $existing    = Get-Content $codexAgents -Raw
        $pattern     = "(?s)" + [regex]::Escape($markerStart) + ".*?" + [regex]::Escape($markerEnd)
        $replacement = "$markerStart`n$zentraSection`n$markerEnd"
        $updated     = [regex]::Replace($existing, $pattern, $replacement)
        Set-Content -Path $codexAgents -Value $updated -Encoding utf8
    } else {
        Add-Content -Path $codexAgents -Value "`n`n$markerStart`n$zentraSection`n$markerEnd" -Encoding utf8
    }

    $script:currentStep++
    Show-Progress -Current $script:currentStep -Total $totalSteps
}

# --- Execute ---
$action = "Installing"
if (($installClaude -and $claudeExists) -or ($installOpenCode -and $opencodeExists) -or ($installCursor -and $cursorExists) -or ($installCodex -and $codexExists)) {
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

if ($installCursor) {
    Install-Cursor
}

if ($installCodex) {
    Install-Codex
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
Write-Host ""
Write-Host "Cursor IDE: Ask the AI 'run zentra-code-recon' - rules are now in ~/.cursor/rules/"
Write-Host "Codex CLI: Ask the AI 'run zentra-code-recon' - native skills are in ~/.codex/skills/ and the plugin is linked at ~/plugins/zentra"
