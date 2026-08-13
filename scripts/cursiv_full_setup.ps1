# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: install-build
# Hash reversed: 94b2e6ff378bd63e9a8a529667e5a281e3014d8844507bf5a675d0cef164d7a8
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: cf590d6e8938bbc7860f9b58fa135f186ee2e9c46565d0b9e3f62bafe4c93d17
# Substrate loop hash: abdfb3b6abe41dffff7cd8152019419e583aba137a89a749102ba3481736ece5
# Substrate loop logic: גדוחדΔדΗגדזΕΒוחחחחΘהואΒΖΓΑΒבΕΒבזΖאΔגדגΒΔΘגאבגΘΕבΒΑΓדגΔΕאΒΘΔΗזהזΖ
# Natural evolution depth: 2
# Exponential evolution rate: 8
# Leaf origin hash: 6d0888513e2e28f5fcfcf662b97fc6080b3d04abee0b0309096771ef64a9e7fd
# Evolution hash: 450ccc251a3f57b162a6ceeba792c266bd6c9982bf18f58ffa2c69fe72bbfbf6
# Evolution logic: ΕΖΑהההΓΖΒגΔחΖΘדΒΗΓגΗהזזדגΘבΓהΓΗΗדוΗהבבאΓדחΒאחΖאחחגΓהΗבחזΘΓדדחדחΗ
# Binary reversed: 1001001011010100011101101111111111001110000111011011011011000111100101010001010110100100100101100110111001111010010101000001100001111100000010000010101100010001001000101010000011101101111110100101011011101010101100000011011111111000011000101011111001010001
# Greek/Hebrew/logic stamp: אגΘוΕΗΒחזהΑוΖΘΗגΖחדΘΑΖΕΕאאוΕΒΑΔזΒאΓגΖזΘΗΗבΓΖגאגבזΔΗודאΘΔחחΗזΓדΕב
# Encoded local stamp: ŪŪ∂ΝīĪ∃ΣμφΣĀΙŪĪΜŪΠŌπζχāληīĀξΛīργŌυεδΙγΗΥτΑĀ=
# CURSIV-CRUCIBLE-STAMP END
# ============================================================
#  Cursiv Full Bootstrap Setup
#  JW Architect Software | Joshua Winkler
#
#  One-click installer: downloads every requirement Cursiv needs.
#  Each component opens its own visible window.
#  Run from the Cursiv install dir or standalone.
# ============================================================

param(
    [string]$CursivDir = $PSScriptRoot,
    [switch]$Silent
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

# ── Resolve Cursiv install directory ─────────────────────────────────────────
if (-not $CursivDir -or -not (Test-Path $CursivDir)) {
    $CursivDir = Split-Path $MyInvocation.MyCommand.Path -Parent
    if ($CursivDir -like "*\scripts") {
        $CursivDir = Split-Path $CursivDir -Parent
    }
}

# ── Helpers ───────────────────────────────────────────────────────────────────

function Write-Banner {
    param([string]$Text, [string]$Color = "Cyan")
    $line = "=" * 60
    Write-Host $line -ForegroundColor $Color
    Write-Host "  $Text" -ForegroundColor $Color
    Write-Host $line -ForegroundColor $Color
}

function Refresh-PATH {
    $machinePath = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
    $userPath    = [System.Environment]::GetEnvironmentVariable("PATH", "User")
    $env:PATH    = "$machinePath;$userPath"
}

function Test-Command { param([string]$Name); return [bool](Get-Command $Name -ErrorAction SilentlyContinue) }

function Open-StepWindow {
    <#
    Opens a new visible PowerShell window that runs $Body, waits for it.
    $Title      — window title (shown in taskbar)
    $Body       — the PowerShell code string to run
    $WaitOnDone — on success, briefly counts down before the window
                  auto-closes, so a successful run doesn't require any
                  keypress (this used to always block on Read-Host — since
                  every step used that default, a single missed window
                  silently stopped every step after it, including the
                  actual model downloads). On failure, the window stays
                  open until the user closes it, instead of vanishing.

    The spawned powershell.exe has no -NoExit, so if $Body hits an error
    that isn't caught by its own try/catch, the process would previously
    just exit — closing the window instantly, before any red error text
    could be read or copied. Body now always runs inside an outer
    try/catch, and its console output is scanned for [ERROR]/[FATAL]/[WARN]
    afterward — if any of those appear (whether from an uncaught exception
    or a step's own caught-and-printed failure), the window requires a
    keypress to close instead of auto-continuing.
    #>
    param(
        [string]$Title,
        [string]$Body,
        [bool]$WaitOnDone = $true
    )

    # $WaitOnDone belongs to THIS process — the wrapped script below runs in
    # a brand-new powershell.exe (-EncodedCommand), so its value must be
    # baked into the text now, not referenced as a variable name (which
    # would resolve to nothing in the child process and evaluate as false).
    $waitOnDoneLiteral = if ($WaitOnDone) { '$true' } else { '$false' }

    $wrapped = @"
`$ErrorActionPreference = 'Continue'
`$__transcript = [System.IO.Path]::GetTempFileName()
Start-Transcript -Path `$__transcript -Force | Out-Null
try {
$Body
} catch {
    Write-Host ''
    Write-Host "[FATAL] Unhandled error: `$_" -ForegroundColor Red
}
Stop-Transcript | Out-Null
`$__log = Get-Content `$__transcript -Raw -ErrorAction SilentlyContinue
Remove-Item `$__transcript -Force -ErrorAction SilentlyContinue

Write-Host ''
if (`$__log -match '\[ERROR\]|\[FATAL\]|\[WARN\]') {
    Write-Host 'One or more issues were reported above (see the [ERROR]/[WARN]/[FATAL] lines).' -ForegroundColor Red
    Write-Host 'This window will stay open — copy the message above, then press ENTER to close it.' -ForegroundColor Red
    Read-Host
} elseif ($waitOnDoneLiteral) {
    Write-Host 'Continuing automatically in 4 seconds...' -ForegroundColor Gray
    Start-Sleep -Seconds 4
}
"@

    $encoded = [Convert]::ToBase64String(
        [System.Text.Encoding]::Unicode.GetBytes($wrapped)
    )

    $proc = Start-Process powershell -ArgumentList @(
        "-NoProfile", "-NoLogo",
        "-WindowStyle", "Normal",
        "-ExecutionPolicy", "Bypass",
        "-EncodedCommand", $encoded
    ) -PassThru

    # Give the window a moment to open, then rename it via win32
    Start-Sleep -Milliseconds 600
    try {
        Add-Type -AssemblyName Microsoft.VisualBasic -ErrorAction SilentlyContinue
        $proc.MainWindowHandle | Out-Null
    } catch {}

    $proc.WaitForExit()
}

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

Clear-Host
Write-Banner "CURSIV FULL SETUP — JW Architect Software"
Write-Host ""
Write-Host "  This will install every requirement for Cursiv in separate windows."
Write-Host "  Each window shows live progress. Do NOT close them manually."
Write-Host ""
Write-Host "  Steps:"
Write-Host "   [1]  winget (Windows Package Manager)"
Write-Host "   [2]  Git for Windows"
Write-Host "   [3]  Python 3.11"
Write-Host "   [4]  Visual C++ Redistributables"
Write-Host "   [5]  Ollama (local AI engine)"
Write-Host "   [6]  Start Ollama service"
Write-Host "   [7]  Pull llama3.1 model  (~4.7 GB — takes a while)"
Write-Host "  [B]   Offline Code Council (optional, ~18 GB)"
Write-Host "   [8]  Python packages (anthropic, openai, PyQt6, etc.)"
Write-Host "   [9]  Windows Terminal (optional, enhances CLI)"
Write-Host "  [10]  PATH verification"
Write-Host "  [11]  Cursiv self-test"
Write-Host "  [12]  Launch Cursiv"
Write-Host ""
Write-Host "  Starting automatically in 4 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 4

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — winget
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "[1/12] Checking winget..." -ForegroundColor Yellow

Open-StepWindow -Title "Cursiv Setup [1/12] — winget" -Body @'
$host.UI.RawUI.WindowTitle = "Cursiv Setup [1/12] — winget"
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  STEP 1 of 12 — Windows Package Manager (winget)" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "[OK] winget is already installed." -ForegroundColor Green
    winget --version
} else {
    Write-Host "winget not found. Installing via App Installer from Microsoft Store..." -ForegroundColor Yellow
    try {
        # Download the App Installer bundle which installs winget
        $uri = "https://aka.ms/getwinget"
        $pkg = "$env:TEMP\AppInstaller.msixbundle"
        Write-Host "Downloading App Installer..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri $uri -OutFile $pkg -UseBasicParsing
        Add-AppxPackage -Path $pkg -ForceApplicationShutdown
        Write-Host "[OK] winget installed." -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Could not auto-install winget: $_" -ForegroundColor Yellow
        Write-Host "Please install it from the Microsoft Store (search 'App Installer')."
    }
}

Write-Host ""
Write-Host "[DONE] Step 1 complete." -ForegroundColor Green
'@

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2 — Git
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "[2/12] Installing Git..." -ForegroundColor Yellow

Open-StepWindow -Title "Cursiv Setup [2/12] — Git" -Body @'
$host.UI.RawUI.WindowTitle = "Cursiv Setup [2/12] — Git for Windows"
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  STEP 2 of 12 — Git for Windows" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$machinePath = [System.Environment]::GetEnvironmentVariable("PATH","Machine")
$userPath    = [System.Environment]::GetEnvironmentVariable("PATH","User")
$env:PATH    = "$machinePath;$userPath"

if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "[OK] Git is already installed: $(git --version)" -ForegroundColor Green
} else {
    Write-Host "Installing Git for Windows via winget..." -ForegroundColor Cyan
    try {
        winget install --id Git.Git --accept-package-agreements --accept-source-agreements --silent
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
        if (Get-Command git -ErrorAction SilentlyContinue) {
            Write-Host "[OK] Git installed: $(git --version)" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Git installed but not on PATH yet — restart may be needed." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[ERROR] Git install failed: $_" -ForegroundColor Red
        Write-Host "Download manually: https://git-scm.com/download/win"
    }
}

Write-Host ""
Write-Host "[DONE] Step 2 complete." -ForegroundColor Green
'@

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — Python 3.11
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "[3/12] Installing Python 3.11..." -ForegroundColor Yellow

Open-StepWindow -Title "Cursiv Setup [3/12] — Python 3.11" -Body @'
$host.UI.RawUI.WindowTitle = "Cursiv Setup [3/12] — Python 3.11"
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  STEP 3 of 12 — Python 3.11" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$machinePath = [System.Environment]::GetEnvironmentVariable("PATH","Machine")
$userPath    = [System.Environment]::GetEnvironmentVariable("PATH","User")
$env:PATH    = "$machinePath;$userPath"

$pyOk = $false
foreach ($cmd in @("python3.11","py -3.11","python")) {
    try {
        $ver = & $cmd.Split()[0] ($cmd.Split() | Select-Object -Skip 1) --version 2>&1
        if ($ver -match "3\.11") { $pyOk = $true; Write-Host "[OK] $ver" -ForegroundColor Green; break }
    } catch {}
}

if (-not $pyOk) {
    Write-Host "Installing Python 3.11 via winget..." -ForegroundColor Cyan
    try {
        winget install --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements --silent
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
        $ver = python --version 2>&1
        Write-Host "[OK] $ver" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Python install failed: $_" -ForegroundColor Red
        Write-Host "Download manually: https://www.python.org/downloads/release/python-3119/"
    }
} else {
    Write-Host "[OK] Python 3.11 already installed." -ForegroundColor Green
}

Write-Host ""
Write-Host "[DONE] Step 3 complete." -ForegroundColor Green
'@

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 4 — Visual C++ Redistributable
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "[4/12] Installing Visual C++ Redistributable..." -ForegroundColor Yellow

Open-StepWindow -Title "Cursiv Setup [4/12] — Visual C++ Runtime" -Body @'
$host.UI.RawUI.WindowTitle = "Cursiv Setup [4/12] — Visual C++ Runtime"
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  STEP 4 of 12 — Microsoft Visual C++ Redistributable 2015-2022" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Required by Python, PyQt6, and many native extensions."
Write-Host ""

try {
    winget install --id Microsoft.VCRedist.2015+.x64 --accept-package-agreements --accept-source-agreements --silent
    Write-Host "[OK] Visual C++ Redistributable installed/verified." -ForegroundColor Green
} catch {
    Write-Host "[WARN] Could not install via winget: $_" -ForegroundColor Yellow
    Write-Host "Trying direct download..."
    try {
        $url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
        $out = "$env:TEMP\vc_redist.x64.exe"
        Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing
        Start-Process $out -ArgumentList "/install", "/quiet", "/norestart" -Wait
        Write-Host "[OK] Visual C++ Redistributable installed." -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Could not install Visual C++ Redistributable: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "[DONE] Step 4 complete." -ForegroundColor Green
'@

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5 — Ollama
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "[5/12] Installing Ollama..." -ForegroundColor Yellow

Open-StepWindow -Title "Cursiv Setup [5/12] — Ollama" -Body @'
$host.UI.RawUI.WindowTitle = "Cursiv Setup [5/12] — Ollama (local AI engine)"
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  STEP 5 of 12 — Ollama (local AI engine)" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$machinePath = [System.Environment]::GetEnvironmentVariable("PATH","Machine")
$userPath    = [System.Environment]::GetEnvironmentVariable("PATH","User")
$env:PATH    = "$machinePath;$userPath"

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "[OK] Ollama already installed: $(ollama --version 2>&1)" -ForegroundColor Green
} else {
    Write-Host "Installing Ollama via winget..." -ForegroundColor Cyan
    $installed = $false
    try {
        winget install --id Ollama.Ollama --accept-package-agreements --accept-source-agreements --silent
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
        if (Get-Command ollama -ErrorAction SilentlyContinue) {
            $installed = $true
            Write-Host "[OK] Ollama installed: $(ollama --version 2>&1)" -ForegroundColor Green
        }
    } catch {}

    if (-not $installed) {
        Write-Host "winget method failed, trying direct download..." -ForegroundColor Yellow
        try {
            $url = "https://ollama.com/download/OllamaSetup.exe"
            $out = "$env:TEMP\OllamaSetup.exe"
            Write-Host "Downloading OllamaSetup.exe (~115 MB)..." -ForegroundColor Cyan
            Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing
            Write-Host "Running Ollama installer..." -ForegroundColor Cyan
            Start-Process $out -ArgumentList "/S" -Wait
            $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
            if (Get-Command ollama -ErrorAction SilentlyContinue) {
                Write-Host "[OK] Ollama installed." -ForegroundColor Green
            } else {
                Write-Host "[WARN] Ollama installer ran but ollama not on PATH yet." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[ERROR] Ollama install failed: $_" -ForegroundColor Red
            Write-Host "Download manually: https://ollama.com/download"
        }
    }
}

Write-Host ""
Write-Host "[DONE] Step 5 complete." -ForegroundColor Green
'@

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 6 — Start Ollama service
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "[6/12] Starting Ollama service..." -ForegroundColor Yellow

Open-StepWindow -Title "Cursiv Setup [6/12] — Start Ollama Service" -WaitOnDone $false -Body @'
$host.UI.RawUI.WindowTitle = "Cursiv Setup [6/12] — Ollama Service"
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  STEP 6 of 12 — Starting Ollama service" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$machinePath = [System.Environment]::GetEnvironmentVariable("PATH","Machine")
$userPath    = [System.Environment]::GetEnvironmentVariable("PATH","User")
$env:PATH    = "$machinePath;$userPath"

# Check if already running
try {
    $resp = Invoke-RestMethod -Uri "http://localhost:11434" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[OK] Ollama service is already running." -ForegroundColor Green
} catch {
    Write-Host "Starting Ollama server in background..." -ForegroundColor Cyan
    Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
    Write-Host "Waiting for Ollama to be ready..."
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 2
        try {
            Invoke-RestMethod -Uri "http://localhost:11434" -TimeoutSec 2 -ErrorAction Stop | Out-Null
            $ready = $true
            break
        } catch {}
        Write-Host "  ...waiting ($($i*2)s)" -ForegroundColor Gray
    }
    if ($ready) {
        Write-Host "[OK] Ollama service is running." -ForegroundColor Green
    } else {
        Write-Host "[WARN] Ollama service did not respond in time. Step 7 may wait longer." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[DONE] Step 6 complete." -ForegroundColor Green
Write-Host "(This window will close automatically)"
Start-Sleep -Seconds 3
'@

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 7 — Pull llama3.1 model
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "[7/12] Pulling llama3.1 model (~4.7 GB — this takes a while)..." -ForegroundColor Yellow

Open-StepWindow -Title "Cursiv Setup [7/12] — llama3.1 Model Download" -Body @'
$host.UI.RawUI.WindowTitle = "Cursiv Setup [7/12] — llama3.1 Download (~4.7 GB)"
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  STEP 7 of 12 — Pull llama3.1 AI model (~4.7 GB)" -ForegroundColor Cyan
Write-Host "  This is a ONE-TIME download. Stored locally forever." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "  You can minimise this window and continue using your PC."
Write-Host "  Do NOT close it — the download will stop."
Write-Host ""

$machinePath = [System.Environment]::GetEnvironmentVariable("PATH","Machine")
$userPath    = [System.Environment]::GetEnvironmentVariable("PATH","User")
$env:PATH    = "$machinePath;$userPath"

# Check if model already present
$models = ollama list 2>&1
if ($models -match "llama3") {
    Write-Host "[OK] llama3 model already downloaded:" -ForegroundColor Green
    Write-Host $models
} else {
    Write-Host "Pulling llama3.1 (4.7 GB) — progress shown below:" -ForegroundColor Cyan
    Write-Host ""
    try {
        ollama pull llama3.1
        # ollama.exe is a native process — a failed pull exits non-zero, it
        # does not throw a catchable PowerShell exception, so try/catch alone
        # would print "[OK]" even on failure. Check the real exit code.
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[OK] llama3.1 model is ready." -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "[ERROR] Model pull failed (exit code $LASTEXITCODE)." -ForegroundColor Red
            Write-Host "You can retry manually: ollama pull llama3.1"
        }
    } catch {
        Write-Host "[ERROR] Model pull failed: $_" -ForegroundColor Red
        Write-Host "You can retry manually: ollama pull llama3.1"
    }
}

Write-Host ""
Write-Host "[DONE] Step 7 complete." -ForegroundColor Green
'@

# ══════════════════════════════════════════════════════════════════════════════
#  BONUS STEP — optional Winkler-Codex models (qwen2.5-coder + deepseek-coder-v2)
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "[Bonus] Offline Code Council (optional, ~18 GB)..." -ForegroundColor Yellow

Open-StepWindow -Title "Cursiv Setup [Bonus] — Offline Code Council" -Body @'
$host.UI.RawUI.WindowTitle = "Cursiv Setup [Bonus] - Offline Code Council"
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  BONUS STEP - Winkler-Codex offline code council" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "  Two specialist coding models that review each other's" -ForegroundColor DarkYellow
Write-Host "  work for higher-quality code output (Winkler-Codex)." -ForegroundColor DarkYellow
Write-Host ""
Write-Host "  qwen2.5-coder:14b       - primary coder   (~8.7 GB)" -ForegroundColor DarkYellow
Write-Host "  deepseek-coder-v2:16b   - critic/reviewer (~9.1 GB)" -ForegroundColor DarkYellow
Write-Host ""
Write-Host "  Total: ~18 GB additional storage needed." -ForegroundColor DarkYellow
Write-Host "  Cursiv works fine without them (uses llama3.1 by default)." -ForegroundColor DarkYellow
Write-Host "  You can also install these later from the launcher." -ForegroundColor DarkYellow
Write-Host ""

$installCode = Read-Host "Download the Offline Code Council now? [y/N]"
if ($installCode -match "^[Yy]") {
    foreach ($codeModel in @("qwen2.5-coder:14b", "deepseek-coder-v2:16b")) {
        Write-Host ""
        Write-Host "Pulling $codeModel (this will take a while)..." -ForegroundColor Cyan
        try {
            ollama pull $codeModel
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK] $codeModel ready." -ForegroundColor Green
            } else {
                Write-Host "[ERROR] Pull failed (exit code $LASTEXITCODE)." -ForegroundColor Red
                Write-Host "You can retry manually: ollama pull $codeModel"
            }
        } catch {
            Write-Host "[ERROR] Pull failed: $_" -ForegroundColor Red
            Write-Host "You can retry manually: ollama pull $codeModel"
        }
    }
    Write-Host ""
    Write-Host "[OK] Offline Code Council installed. Cursiv will use it automatically for coding questions." -ForegroundColor Green
} else {
    Write-Host "  Skipped. To install later, run in a terminal:" -ForegroundColor DarkGray
    Write-Host "    ollama pull qwen2.5-coder:14b" -ForegroundColor White
    Write-Host "    ollama pull deepseek-coder-v2:16b" -ForegroundColor White
    Write-Host "  ...or use the 'Download Winkler-Codex' button in the launcher." -ForegroundColor White
}

Write-Host ""
Write-Host "[DONE] Bonus step complete." -ForegroundColor Green
'@


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 8 — pip packages
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "[8/12] Installing Python packages..." -ForegroundColor Yellow

Open-StepWindow -Title "Cursiv Setup [8/12] — Python Packages" -Body @'
$host.UI.RawUI.WindowTitle = "Cursiv Setup [8/12] — Python Packages"
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  STEP 8 of 12 — Python packages" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$machinePath = [System.Environment]::GetEnvironmentVariable("PATH","Machine")
$userPath    = [System.Environment]::GetEnvironmentVariable("PATH","User")
$env:PATH    = "$machinePath;$userPath"

# Upgrade pip first
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet

$packages = @(
    "PyQt6>=6.7.0",
    "anthropic>=0.30.0",
    "openai>=1.30.0",
    "httpx>=0.27.0",
    "psutil>=5.9.0",
    "bcrypt>=4.0.0",
    "PyJWT>=2.8.0",
    "passlib[bcrypt]>=1.7.4",
    "python-jose[cryptography]>=3.3.0",
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "pydantic>=2.0.0",
    "Pillow>=10.0.0",
    "pywin32>=306",
    "websockets>=12.0",
    "requests>=2.31.0",
    "aiofiles>=23.2.1"
)

Write-Host ""
Write-Host "Installing $($packages.Count) packages:" -ForegroundColor Cyan
foreach ($pkg in $packages) {
    Write-Host "  -> $pkg" -ForegroundColor Gray
}
Write-Host ""

$failed = @()
foreach ($pkg in $packages) {
    $name = ($pkg -split "[>=<]")[0]
    Write-Host "Installing $name..." -ForegroundColor Yellow -NoNewline
    try {
        python -m pip install "$pkg" --quiet 2>&1 | Out-Null
        Write-Host "  [OK]" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL]" -ForegroundColor Red
        $failed += $pkg
    }
}

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "The following packages failed to install:" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "Run manually: pip install <package>" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "[OK] All packages installed successfully." -ForegroundColor Green
}

Write-Host ""
Write-Host "[DONE] Step 8 complete." -ForegroundColor Green
'@

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 9 — Windows Terminal (optional)
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "[9/12] Installing Windows Terminal (optional)..." -ForegroundColor Yellow

Open-StepWindow -Title "Cursiv Setup [9/12] — Windows Terminal" -Body @'
$host.UI.RawUI.WindowTitle = "Cursiv Setup [9/12] — Windows Terminal (optional)"
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  STEP 9 of 12 — Windows Terminal (optional)" -ForegroundColor Cyan
Write-Host "  Provides the best experience for Cursiv CLI mode." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$wt = Get-AppxPackage -Name "Microsoft.WindowsTerminal" -ErrorAction SilentlyContinue
if ($wt) {
    Write-Host "[OK] Windows Terminal is already installed ($($wt.Version))." -ForegroundColor Green
} else {
    Write-Host "Installing Windows Terminal via winget..." -ForegroundColor Cyan
    try {
        winget install --id Microsoft.WindowsTerminal --accept-package-agreements --accept-source-agreements --silent
        Write-Host "[OK] Windows Terminal installed." -ForegroundColor Green
    } catch {
        Write-Host "[SKIP] Could not install Windows Terminal: $_" -ForegroundColor Yellow
        Write-Host "This is optional — Cursiv works with any terminal."
    }
}

Write-Host ""
Write-Host "[DONE] Step 9 complete." -ForegroundColor Green
'@

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 10 — PATH verification
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "[10/12] Verifying PATH and environment..." -ForegroundColor Yellow

Open-StepWindow -Title "Cursiv Setup [10/12] — PATH Verification" -Body @'
$host.UI.RawUI.WindowTitle = "Cursiv Setup [10/12] — PATH Verification"
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  STEP 10 of 12 — PATH and Environment Verification" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$machinePath = [System.Environment]::GetEnvironmentVariable("PATH","Machine")
$userPath    = [System.Environment]::GetEnvironmentVariable("PATH","User")
$env:PATH    = "$machinePath;$userPath"

$checks = @{
    "git"    = "Git"
    "python" = "Python"
    "pip"    = "pip"
    "ollama" = "Ollama"
}

$allOk = $true
foreach ($cmd in $checks.Keys) {
    $label = $checks[$cmd]
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($found) {
        try {
            $ver = & $cmd --version 2>&1 | Select-Object -First 1
        } catch { $ver = "installed" }
        Write-Host "  [OK]  $label — $ver" -ForegroundColor Green
    } else {
        Write-Host "  [!!]  $label — NOT FOUND on PATH" -ForegroundColor Red
        $allOk = $false
    }
}

Write-Host ""
if ($allOk) {
    Write-Host "[OK] All tools found on PATH." -ForegroundColor Green
} else {
    Write-Host "[WARN] Some tools not found. A system restart may be needed to refresh PATH." -ForegroundColor Yellow
    Write-Host "After restarting, Cursiv should work correctly."
}

Write-Host ""
Write-Host "[DONE] Step 10 complete." -ForegroundColor Green
'@

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 11 — Cursiv self-test
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "[11/12] Running Cursiv self-test..." -ForegroundColor Yellow

$cursivExe = Join-Path $CursivDir "Cursiv.exe"
$testScript = @"
`$host.UI.RawUI.WindowTitle = "Cursiv Setup [11/12] — Self-Test"
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  STEP 11 of 12 — Cursiv Self-Test" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

`$machinePath = [System.Environment]::GetEnvironmentVariable("PATH","Machine")
`$userPath    = [System.Environment]::GetEnvironmentVariable("PATH","User")
`$env:PATH    = "`$machinePath;`$userPath"

`$cursivExe = "$($cursivExe -replace "'","''")"

# Test 1: Cursiv.exe exists
if (Test-Path `$cursivExe) {
    Write-Host "[OK] Cursiv.exe found at: `$cursivExe" -ForegroundColor Green
} else {
    Write-Host "[!!] Cursiv.exe not found at: `$cursivExe" -ForegroundColor Red
    Write-Host "     The Cursiv bundle may not be fully installed."
}

# Test 2: Python imports
Write-Host ""
Write-Host "Testing Python package imports..." -ForegroundColor Cyan
`$imports = @("PyQt6","anthropic","openai","httpx","psutil","bcrypt","fastapi","uvicorn","pydantic")
foreach (`$imp in `$imports) {
    `$result = python -c "import `$imp; print('ok')" 2>&1
    if (`$result -match "ok") {
        Write-Host "  [OK]  `$imp" -ForegroundColor Green
    } else {
        Write-Host "  [!!]  `$imp — `$result" -ForegroundColor Red
    }
}

# Test 3: Ollama reachable
Write-Host ""
Write-Host "Testing Ollama service..." -ForegroundColor Cyan
try {
    `$resp = Invoke-RestMethod -Uri "http://localhost:11434" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  [OK]  Ollama service is running." -ForegroundColor Green
} catch {
    Write-Host "  [!!]  Ollama not reachable at localhost:11434" -ForegroundColor Yellow
    Write-Host "        Run 'ollama serve' to start it."
}

Write-Host ""
Write-Host "[DONE] Step 11 complete." -ForegroundColor Green
"@

Open-StepWindow -Title "Cursiv Setup [11/12] — Self-Test" -Body $testScript

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 12 — Launch Cursiv
# ══════════════════════════════════════════════════════════════════════════════

Write-Host "[12/12] Setup complete — launching Cursiv!" -ForegroundColor Green
Write-Host ""

Open-StepWindow -Title "Cursiv Setup [12/12] — Complete!" -WaitOnDone $false -Body @"
`$host.UI.RawUI.WindowTitle = "Cursiv Setup — Complete!"
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  SETUP COMPLETE — Cursiv is ready!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""
Write-Host "  Every requirement has been installed and verified." -ForegroundColor White
Write-Host ""
Write-Host "  Launching Cursiv now..." -ForegroundColor Cyan
Write-Host ""

`$exe = "$($cursivExe -replace "'","''")"
if (Test-Path `$exe) {
    Start-Process `$exe
    Write-Host "  Cursiv launched!" -ForegroundColor Green
} else {
    Write-Host "  Could not find Cursiv.exe at: `$exe" -ForegroundColor Red
    Write-Host "  Navigate to your Cursiv install folder and run Cursiv.exe manually."
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "  JW Architect Software | Joshua Winkler" -ForegroundColor DarkCyan
Write-Host "  Cursiv — Offline AI Workspace" -ForegroundColor DarkCyan
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 5
"@

Write-Host ""
Write-Banner "ALL STEPS COMPLETE" "Green"
Write-Host ""
Write-Host "  Cursiv has been fully set up." -ForegroundColor White
Write-Host "  If you see any [!!] warnings above, restart your PC and try again." -ForegroundColor Gray
Write-Host ""
