# setup_windows.ps1 - WorkBuddy daily auto check-in, one-shot installer (Windows)
#
# Repo: https://github.com/Alice9245426/workbuddy-auto-checkin
# License: MIT
# Upstream signin script: https://github.com/88lin/workbuddy-auto-signin (MIT, referenced, not copied)
#
# Usage (run in the repo root):
#   powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1 -SkipRegister   # self-check only
#   powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1                 # full install
#
# Optional:
#   -SigninDir "D:\path\workbuddy-auto-signin"   reuse an existing upstream clone
#   -Pythonw   "C:\path\pythonw.exe"            force a specific interpreter
#   -MainAt    "00:00"                          main daily check-in time
#
# Creates two scheduled tasks:
#   WorkBuddyAutoSignin   daily at -MainAt (default 00:00) -> silent signin + growth center
#   WorkBuddyGrowthPoll   daily 01/05/09/13/17/21           -> catch-up signin + growth center
#
# All output is ASCII-only on purpose: Windows PowerShell 5.1 misreads UTF-8
# scripts without a BOM. No secret is ever printed.

param(
    [string]$SigninDir = "",
    [string]$Pythonw = "",
    [string]$MainAt = "00:00",
    [switch]$SkipRegister
)

$ErrorActionPreference = "Stop"
# Invoke-WebRequest / Expand-Archive would otherwise flood the console with
# progress bars on a fresh install, which looks like a hang to a first-time user.
$ProgressPreference = "SilentlyContinue"
# The upstream script prints UTF-8 Chinese; PowerShell 5.1 decodes native stdout
# with the ANSI code page by default, which garbles it.
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    $env:PYTHONIOENCODING = "utf-8"
    & cmd /c "chcp 65001 >nul 2>&1"
} catch { }
$DefaultDir = Join-Path $env:LOCALAPPDATA "WorkBuddyAutoCheckin"
$Upstream = "https://github.com/88lin/workbuddy-auto-signin.git"
$UpstreamZip = "https://api.github.com/repos/88lin/workbuddy-auto-signin/zipball/main"

function Say([string]$msg, [string]$color = "Gray") { Write-Host $msg -ForegroundColor $color }

function Find-Pythonw {
    $c = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
    if ($c -and (Test-Path -LiteralPath $c)) { return $c }

    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($py) {
        # Skip the Windows Store stub (0-byte / App Execution Alias).
        if (-not ($py -like "*WindowsApps*")) {
            $c = Join-Path (Split-Path $py) "pythonw.exe"
            if (Test-Path -LiteralPath $c) { return $c }
        }
    }
    foreach ($pat in @(
        "$env:LOCALAPPDATA\Programs\Python\Python3*\pythonw.exe",
        "C:\Python3*\pythonw.exe",
        "C:\Program Files\Python3*\pythonw.exe",
        "$env:USERPROFILE\.workbuddy\binaries\python\versions\*\pythonw.exe",
        "$env:USERPROFILE\.workbuddy\binaries\python\envs\*\Scripts\pythonw.exe"
    )) {
        $hit = Get-ChildItem $pat -ErrorAction SilentlyContinue |
               Sort-Object FullName -Descending | Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }
    $launcher = Join-Path $env:SystemRoot "py.exe"
    if (Test-Path -LiteralPath $launcher) {
        try {
            $exe = (& $launcher -3 -c "import sys;print(sys.executable)" 2>$null | Select-Object -Last 1)
            if ($exe) {
                $c = Join-Path (Split-Path $exe.Trim()) "pythonw.exe"
                if (Test-Path -LiteralPath $c) { return $c }
            }
        } catch { }
    }
    return $null
}

function Get-PythonExe([string]$pythonwPath) {
    $c = Join-Path (Split-Path $pythonwPath) "python.exe"
    if (Test-Path -LiteralPath $c) { return $c }
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($py -and -not ($py -like "*WindowsApps*")) { return $py }
    return $null
}

function Ensure-Upstream([string]$dir) {
    $signin = Join-Path $dir "signin.py"
    if (Test-Path -LiteralPath $signin) {
        Say ("[2/5] Upstream script found: " + $signin) "Green"
        return $signin
    }
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Say "[2/5] Fetching upstream signin script ..." "Cyan"
    $ok = $false
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git) {
        try {
            & $git.Source clone --depth 1 $Upstream $dir 2>$null | Out-Null
            if (Test-Path -LiteralPath (Join-Path $dir "signin.py")) { $ok = $true }
        } catch { }
    }
    if (-not $ok) {
        # git endpoint may be blocked on campus networks; api.github.com usually works.
        Say "      git clone failed, trying GitHub API zip fallback ..." "Yellow"
        try {
            $zip = Join-Path $env:TEMP "wb-signin-upstream.zip"
            $extract = Join-Path $env:TEMP "wb-signin-extract"
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $UpstreamZip -OutFile $zip -UseBasicParsing -TimeoutSec 90 `
                -Headers @{ "User-Agent" = "workbuddy-auto-checkin" }
            if (Test-Path -LiteralPath $extract) { Remove-Item -LiteralPath $extract -Recurse -Force }
            Expand-Archive -LiteralPath $zip -DestinationPath $extract -Force
            $inner = Get-ChildItem -LiteralPath $extract -Directory | Select-Object -First 1
            if ($inner) {
                Copy-Item -Path (Join-Path $inner.FullName "*") -Destination $dir -Recurse -Force
            }
            Remove-Item -LiteralPath $zip -Force -ErrorAction SilentlyContinue
            if (Test-Path -LiteralPath (Join-Path $dir "signin.py")) { $ok = $true }
        } catch {
            Say ("      zip fallback failed: " + $_.Exception.Message) "Red"
        }
    }
    if (-not $ok) {
        Say "Cannot fetch upstream. Download it manually:" "Red"
        Say ("  " + $Upstream) "Yellow"
        Say ("  then extract into: " + $dir) "Yellow"
        exit 1
    }
    Say ("      saved to " + $dir) "Green"
    return (Join-Path $dir "signin.py")
}

Say ""
Say "WorkBuddy Auto Check-in - one-shot setup" "Cyan"
Say ("-" * 52) "DarkGray"

# --- 1. pythonw (fail fast before any network access) ---
Say "[1/5] Locating pythonw.exe ..." -NoNewline
if (-not $Pythonw -or -not (Test-Path -LiteralPath $Pythonw)) { $Pythonw = Find-Pythonw }
if (-not $Pythonw -or -not (Test-Path -LiteralPath $Pythonw)) {
    Say " FAILED" "Red"
    Say "Python 3 not found. Install from https://www.python.org/downloads/ (check 'Add to PATH')," "Yellow"
    Say "or pass -Pythonw with the full path to pythonw.exe." "Yellow"
    exit 1
}
Say (" " + $Pythonw) "Green"

$pyExe = Get-PythonExe $Pythonw
if (-not $pyExe) {
    Say "python.exe not found next to pythonw.exe. Reinstall Python 3." "Red"
    exit 1
}

# --- 2. upstream ---
$targetDir = $DefaultDir
if ($SigninDir) { $targetDir = $SigninDir }
$signin = Ensure-Upstream $targetDir
$signin = (Resolve-Path -LiteralPath $signin).Path

# --- 3. offline doctor ---
# The upstream script prints a UTF-8 JSON with Chinese text. Under Windows PowerShell
# 5.1 that text may be decoded as GBK, which can even swallow a quote and break the
# JSON. So never parse or echo the raw output: extract only ASCII fields via regex.
function Pick([string]$raw, [string]$key, [string]$fallback) {
    $m = [regex]::Match($raw, '"' + $key + '"\s*:\s*("?)([A-Za-z0-9_./\\:-]+)\1')
    if ($m.Success) { return $m.Groups[2].Value }
    return $fallback
}

Say "[3/5] Offline self-check (doctor) ..." "Cyan"
$doctorRaw = (& $pyExe $signin doctor 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) {
    Say "doctor failed. Make sure the WorkBuddy desktop client is installed and you have logged in once." "Red"
    Say "If WorkBuddy is in a custom folder, set WORKBUDDY_EXE to its full path and retry." "Yellow"
    exit 1
}
Say ("      result=" + (Pick $doctorRaw "result" "?") +
     " | credential_format=" + (Pick $doctorRaw "credential_format" "?") +
     " | electron=" + (Pick $doctorRaw "electron_version" "?")) "DarkGray"
Say "      doctor OK" "Green"

# --- 4. read-only status (decrypt + query, does NOT claim) ---
Say "[4/5] Read-only status check (no claim) ..." "Cyan"
$statusRaw = (& $pyExe $signin status 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) {
    Say "status failed. Open the WorkBuddy client once to refresh the login session, then retry." "Red"
    exit 1
}
$http = Pick $statusRaw "http" "?"
if ($http -ne "200") {
    Say ("      unexpected HTTP status: " + $http) "Red"
    Say "The login session may have expired. Open the WorkBuddy client once, then retry." "Yellow"
    exit 1
}
Say ("      http=200 | today_checked_in=" + (Pick $statusRaw "today_checked_in" "?") +
     " | streak_days=" + (Pick $statusRaw "streak_days" "?") +
     " | total_credits=" + (Pick $statusRaw "total_credits" "?")) "DarkGray"
Say "      status OK (login session is valid)" "Green"

if ($SkipRegister) {
    Say ("-" * 52) "DarkGray"
    Say "SELF-CHECK PASSED. No scheduled task was created (SkipRegister)." "Green"
    Say "Run again without -SkipRegister to install." "Cyan"
    Say ""
    exit 0
}

# --- 5. register scheduled tasks ---
Say "[5/5] Registering scheduled tasks ..." "Cyan"
try {
    $userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    if (-not $userId) { $userId = "$env:USERDOMAIN\$env:USERNAME" }
    $principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive `
        -RunLevel Limited -ErrorAction Stop

    $act1 = New-ScheduledTaskAction -Execute $Pythonw -Argument "`"$signin`" silent" -ErrorAction Stop
    $tri1 = New-ScheduledTaskTrigger -Daily -At $MainAt -ErrorAction Stop
    $set1 = New-ScheduledTaskSettingsSet -StartWhenAvailable -Hidden `
            -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries `
            -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -ErrorAction Stop
    Register-ScheduledTask -TaskName "WorkBuddyAutoSignin" -TaskPath "\" `
        -Action $act1 -Trigger $tri1 -Settings $set1 -Principal $principal `
        -Description "WorkBuddy daily auto check-in (silent, zero AI token)" -Force -ErrorAction Stop | Out-Null

    $tri2 = @()
    foreach ($hh in @("01:00", "05:00", "09:00", "13:00", "17:00", "21:00")) {
        $tri2 += New-ScheduledTaskTrigger -Daily -At $hh -ErrorAction Stop
    }
    $act2 = New-ScheduledTaskAction -Execute $Pythonw -Argument "`"$signin`" silent-poll" -ErrorAction Stop
    $set2 = New-ScheduledTaskSettingsSet -StartWhenAvailable -Hidden `
            -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries `
            -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -ErrorAction Stop
    Register-ScheduledTask -TaskName "WorkBuddyGrowthPoll" -TaskPath "\" `
        -Action $act2 -Trigger $tri2 -Settings $set2 -Principal $principal `
        -Description "WorkBuddy catch-up check-in + growth center poll" -Force -ErrorAction Stop | Out-Null

    $results = @()
    foreach ($tn in @("WorkBuddyAutoSignin", "WorkBuddyGrowthPoll")) {
        $t = Get-ScheduledTask -TaskName $tn -TaskPath "\" -ErrorAction Stop
        $info = Get-ScheduledTaskInfo -TaskName $tn -TaskPath "\" -ErrorAction Stop
        $results += [pscustomobject]@{ Name = $tn; State = $t.State; Next = $info.NextRunTime }
    }
} catch {
    Say ("FAILED: " + $_.Exception.Message) "Red"
    Say "If access is denied (0x80070005), open PowerShell as administrator with the SAME Windows account." "Yellow"
    exit 1
}

Say ("-" * 52) "DarkGray"
Say "INSTALL COMPLETE - both tasks are ready:" "Green"
foreach ($r in $results) {
    Say ("  {0,-22} state={1,-8} next={2}" -f $r.Name, $r.State, $r.Next) "Gray"
}
$logFile = Join-Path (Split-Path -LiteralPath $signin) "signin.log"
Say ("Log: " + $logFile) "Cyan"
Say "Verify a real run:" "DarkGray"
Say "  Start-ScheduledTask -TaskName `"WorkBuddyAutoSignin`"; Get-ScheduledTaskInfo -TaskName `"WorkBuddyAutoSignin`"" "DarkGray"
Say "Uninstall:" "DarkGray"
Say "  Unregister-ScheduledTask -TaskName `"WorkBuddyAutoSignin`" -Confirm:`$false" "DarkGray"
Say "  Unregister-ScheduledTask -TaskName `"WorkBuddyGrowthPoll`" -Confirm:`$false" "DarkGray"
Say ""
