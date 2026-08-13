# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: install-build
# Hash reversed: 7710436e6277ca5c7460446d4757febdf511c95dc1538595482f29f530baf416
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: 4894102967268faec78640e7e67d6c228e60a275fd5ff4e7ba3c8fe9e10dcf38
# Substrate loop hash: 7523bd0cb92a4290b74dfaa99c5cc8bec55f73a90c6c212d87c981eb8d4dd53b
# Substrate loop logic: ΘΖΓΔדוΑהדבΓגΕΓבΑדΘΕוחגגבבהΖההאדזהΖΖחΘΔגבΑהΗהΓΒΓואΘהבאΒזדאוΕווΖΔד
# Natural evolution depth: 2
# Exponential evolution rate: 8
# Leaf origin hash: 018f6ecd2ee6b086856cf5067a6dfd09b6e8efe21e3145c14f4d56fdefc0ad6d
# Evolution hash: 745fd1fc6cd8f965cf5350b63830e31b85d2b54ac22950465d7c29895e7b6ca0
# Evolution logic: ΘΕΖחוΒחהΗהואחבΗΖהחΖΔΖΑדΗΔאΔΑזΔΒדאΖוΓדΖΕגהΓΓבΖΑΕΗΖוΘהΓבאבΖזΘדΗהגΑ
# Binary reversed: 1110111010000000001011000110011101100100111011100011010110100011111000100110000000100010011010110010111010101110111101111101101111111010100010000011100110101011001110001010110000011010100110100010000101001111010010011111101011000000110101011111001010000110
# Greek/Hebrew/logic stamp: ΗΒΕחגדΑΔΖחבΓחΓאΕΖבΖאΔΖΒהוΖבהΒΒΖחודזחΘΖΘΕוΗΕΕΑΗΕΘהΖגהΘΘΓΗזΗΔΕΑΒΘΘ
# Encoded local stamp: ∀∃∃ΩΘ∃γιβΑτīδΟΞγχŪΝΟλ∇βΥΦΦĒŌΑΟδīāΙαιΟΧŪω∞νε=
# CURSIV-CRUCIBLE-STAMP END
# ============================================================
# Cursiv — Ollama Bootstrap
# Runs automatically after the Cursiv installer finishes.
#
# What this does:
#   1. Checks if Ollama is already installed
#   2. If not: downloads OllamaSetup.exe (~90 MB) and installs it silently
#   3. Waits for the Ollama service to start
#   4. Checks if llama3.1 is already pulled
#   5. If not: pulls llama3.1 (~4.7 GB) — this is the slow part
#
# You can close this window safely — if Ollama is already installing
# the model pull will be queued and continue in the background.
# ============================================================

$Host.UI.RawUI.WindowTitle = "Cursiv — AI Setup"
$ErrorActionPreference = "Continue"

$OLLAMA_DOWNLOAD = "https://ollama.com/download/OllamaSetup.exe"
$OLLAMA_MODEL    = "llama3.1"
$SETUP_EXE       = Join-Path $env:TEMP "OllamaSetup.exe"
$OLLAMA_DIR      = Join-Path $env:LOCALAPPDATA "Programs\Ollama"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "  >> $msg" -ForegroundColor Cyan
}

function Write-OK($msg) {
    Write-Host "  [OK] $msg" -ForegroundColor Green
}

function Write-Warn($msg) {
    Write-Host "  [!]  $msg" -ForegroundColor Yellow
}

function Write-Err($msg) {
    Write-Host "  [X]  $msg" -ForegroundColor Red
}

function Find-Ollama {
    if (Get-Command ollama -ErrorAction SilentlyContinue) { return (Get-Command ollama).Source }
    $local = Join-Path $OLLAMA_DIR "ollama.exe"
    if (Test-Path $local) { return $local }
    return $null
}

function Add-OllamaToPath {
    if (Test-Path $OLLAMA_DIR) {
        $env:PATH = "$OLLAMA_DIR;$env:PATH"
    }
}

function Wait-OllamaService($maxWaitS = 30) {
    Write-Step "Waiting for Ollama service to start..."
    $elapsed = 0
    while ($elapsed -lt $maxWaitS) {
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:11434" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            Write-OK "Ollama service is running."
            return $true
        } catch { }
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-Host "  ." -NoNewline
    }
    Write-Host ""
    Write-Warn "Ollama service did not respond in ${maxWaitS}s. Attempting pull anyway..."
    return $false
}

function Is-ModelPresent($model) {
    try {
        $list = & ollama list 2>$null
        return ($list -match [regex]::Escape($model))
    } catch {
        return $false
    }
}

# ── Header ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor DarkYellow
Write-Host "  ║   Cursiv — AI Engine Setup                        ║" -ForegroundColor DarkYellow
Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor DarkYellow
Write-Host ""
Write-Host "  This window sets up the local AI engine for Cursiv."
Write-Host "  You can minimise this — it will finish on its own."
Write-Host ""

# ── Step 1: Install Ollama ────────────────────────────────────────────────────
Write-Step "Checking for Ollama..."
$ollamaExe = Find-Ollama

if ($ollamaExe) {
    Write-OK "Ollama already installed at: $ollamaExe"
    Add-OllamaToPath
} else {
    Write-Step "Ollama not found. Downloading installer (~90 MB)..."
    try {
        $ProgressPreference = "SilentlyContinue"   # faster download
        Invoke-WebRequest -Uri $OLLAMA_DOWNLOAD -OutFile $SETUP_EXE -UseBasicParsing
        $ProgressPreference = "Continue"
        Write-OK "Download complete."
    } catch {
        Write-Err "Download failed: $_"
        Write-Warn "Please download Ollama manually from https://ollama.com/download"
        Write-Host ""
        Write-Host "  Press Enter to close..." -NoNewline
        Read-Host
        exit 1
    }

    Write-Step "Installing Ollama silently..."
    try {
        $proc = Start-Process -FilePath $SETUP_EXE `
            -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART" `
            -Wait -PassThru
        if ($proc.ExitCode -ne 0) {
            throw "Installer exited with code $($proc.ExitCode)"
        }
        Add-OllamaToPath
        Write-OK "Ollama installed."
    } catch {
        Write-Err "Ollama installation failed: $_"
        Write-Host ""
        Write-Host "  Press Enter to close..." -NoNewline
        Read-Host
        exit 1
    }
}

# ── Step 2: Wait for Ollama service ──────────────────────────────────────────
Wait-OllamaService

# ── Step 3: Pull llama3.1 ────────────────────────────────────────────────────
Write-Step "Checking for $OLLAMA_MODEL model..."

if (Is-ModelPresent $OLLAMA_MODEL) {
    Write-OK "$OLLAMA_MODEL already present — nothing to download."
} else {
    Write-Host ""
    Write-Host "  Pulling $OLLAMA_MODEL (~4.7 GB)." -ForegroundColor Cyan
    Write-Host "  Download speed depends on your connection." -ForegroundColor DarkGray
    Write-Host "  A fast connection (100 Mbps) takes ~6 min." -ForegroundColor DarkGray
    Write-Host "  A slower connection (20 Mbps) may take ~30 min." -ForegroundColor DarkGray
    Write-Host ""

    & ollama pull $OLLAMA_MODEL

    if ($LASTEXITCODE -eq 0) {
        Write-OK "$OLLAMA_MODEL is ready."
    } else {
        Write-Warn "Model pull returned exit code $LASTEXITCODE."
        Write-Warn "If the download was interrupted, run this in a terminal:"
        Write-Host "    ollama pull $OLLAMA_MODEL" -ForegroundColor White
    }
}

# ── Step 4: Pull Code Council models (optional, user prompted) ───────────────
Write-Host ""
Write-Host "  ┌──────────────────────────────────────────────────┐" -ForegroundColor DarkYellow
Write-Host "  │  Optional: Offline Code Council                   │" -ForegroundColor DarkYellow
Write-Host "  │  Two specialist coding models that review each    │" -ForegroundColor DarkYellow
Write-Host "  │  other's work for higher-quality code output.     │" -ForegroundColor DarkYellow
Write-Host "  │                                                    │" -ForegroundColor DarkYellow
Write-Host "  │  qwen2.5-coder:14b   — primary coder   (~8.7 GB) │" -ForegroundColor DarkYellow
Write-Host "  │  deepseek-coder-v2:16b — critic/review (~9.1 GB) │" -ForegroundColor DarkYellow
Write-Host "  │                                                    │" -ForegroundColor DarkYellow
Write-Host "  │  Total: ~18 GB additional storage needed.         │" -ForegroundColor DarkYellow
Write-Host "  │  Cursiv works fine without them (uses llama3.1).  │" -ForegroundColor DarkYellow
Write-Host "  └──────────────────────────────────────────────────┘" -ForegroundColor DarkYellow
Write-Host ""
$installCode = Read-Host "  Download Code Council models now? [Y/N]"
if ($installCode -match "^[Yy]") {
    foreach ($codeModel in @("qwen2.5-coder:14b", "deepseek-coder-v2:16b")) {
        if (Is-ModelPresent $codeModel) {
            Write-OK "$codeModel already present."
        } else {
            Write-Step "Pulling $codeModel (this will take a while)..."
            & ollama pull $codeModel
            if ($LASTEXITCODE -eq 0) {
                Write-OK "$codeModel ready."
            } else {
                Write-Warn "Pull failed — run manually: ollama pull $codeModel"
            }
        }
    }
    Write-OK "Code Council models installed. Cursiv will use them automatically for coding questions."
} else {
    Write-Host "  Skipped. To install later, run in a terminal:" -ForegroundColor DarkGray
    Write-Host "    ollama pull qwen2.5-coder:14b" -ForegroundColor White
    Write-Host "    ollama pull deepseek-coder-v2:16b" -ForegroundColor White
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║   Cursiv AI engine is ready.                      ║" -ForegroundColor Green
Write-Host "  ║   Launch Cursiv from the Start Menu or desktop.   ║" -ForegroundColor Green
Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  This window will close in 10 seconds..."
Start-Sleep -Seconds 10
