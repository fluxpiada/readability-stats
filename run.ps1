# run.ps1 — one-command runner for readability-stats, on Windows.
#
#   .\run.ps1                        interactive menu, asks for the folder
#   .\run.ps1 01 C:\path\to\text     run step 01 on that folder
#   .\run.ps1 all C:\path\to\text    run every step in order
#
# Installs uv (astral.sh) if it is missing, then lets uv handle Python and deps.
# The macOS/Linux twin of this script is run.sh; keep the two in step.
#
# NOT YET TESTED ON WINDOWS: written and reviewed against run.sh, but only ever
# run from macOS. Please report anything that breaks, with your PowerShell
# version ($PSVersionTable.PSVersion).

param(
    [string]$Choice = "",
    [string]$Folder = ""
)

$ErrorActionPreference = "Stop"

# PowerShell 7.2 turns anything a native command writes to stderr into a
# terminating error while ErrorActionPreference is Stop, and uv reports progress
# there. Exit codes are what we actually check, so switch that off where it
# exists (7.3+ already defaults to false; 5.1 has no such variable).
if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

Set-Location $PSScriptRoot

# --- 1. make sure uv is available -------------------------------------------
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found - installing from astral.sh ..."
    # Windows PowerShell 5.1 may still default to TLS 1.0, which astral.sh refuses.
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    # the installer drops uv in %USERPROFILE%\.local\bin
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "uv still not on PATH. Open a new PowerShell window and re-run .\run.ps1"
        exit 1
    }
}

# --- 2. sync the environment (downloads Python 3.12 if needed) --------------
# --inexact: this venv is shared with nl/, which may have a larger spaCy model
# installed from the nl-md or nl-lg group. A sync is exact about the groups it
# is given, so without this flag it would uninstall that model every run.
uv sync --quiet --inexact
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# --- 3. figure out what to run ----------------------------------------------
$Steps = @(
    "01_readability.py"
    "02_convert_md_txt.py"
    "03_readability_vs_story_order.py"
    "04_sentence_length_histo.py"
    "05_lexical_div.py"
    "06_complex_deltas.py"
    "07_tightening.py"
    "08_report.py"
    "countwords.py"
)

if (-not $Choice) {
    Write-Host ""
    Write-Host "readability-stats"
    Write-Host "-----------------"
    for ($i = 0; $i -lt $Steps.Count; $i++) {
        Write-Host ("  {0}) {1}" -f ($i + 1), $Steps[$i])
    }
    Write-Host "  a) all of the above"
    Write-Host ""
    $Choice = Read-Host "Choose [1-$($Steps.Count) or a]"
}

if (-not $Folder) {
    Write-Host '(tip: in Explorer, Shift+right-click the folder -> "Copy as path", then paste it here)'
    $Folder = Read-Host "Folder with your .md / .docx files"
}

# A pasted path arrives literally, so the quotes that "Copy as path" wraps it in
# are still attached, and ~ has not been expanded by anything.
$Folder = $Folder.Trim()
if ($Folder.Length -ge 2) {
    foreach ($q in @('"', "'")) {
        if ($Folder.StartsWith($q) -and $Folder.EndsWith($q)) {
            $Folder = $Folder.Substring(1, $Folder.Length - 2)
        }
    }
}
if ($Folder.StartsWith("~")) { $Folder = $HOME + $Folder.Substring(1) }
# Drop a trailing separator, but never off a bare drive root: "C:\" trimmed to
# "C:" means "wherever I last was on C:", which is not what was typed.
if ($Folder -notmatch '^[A-Za-z]:[\\/]?$') {
    $Folder = $Folder.TrimEnd([char[]]@('\', '/'))
}

if (-not (Test-Path -LiteralPath $Folder -PathType Container)) {
    Write-Host ""
    Write-Host "Not a folder: $Folder"
    Write-Host "Pass an existing directory of .md / .docx files, e.g."
    Write-Host "  .\run.ps1 $Choice `"$env:USERPROFILE\Documents\my-book\manuscript`""
    exit 1
}

function Invoke-Step($script) {
    Write-Host ""
    Write-Host "==> $script"
    uv run $script $Folder
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if ($Choice -match '^(a|all|A)$') {
    foreach ($s in $Steps) { Invoke-Step $s }
} else {
    # The step list is the bound, so adding a tenth step needs no edit here.
    $number = 0
    if ([int]::TryParse($Choice, [ref]$number) -and $number -ge 1 -and $number -le $Steps.Count) {
        Invoke-Step $Steps[$number - 1]
    } else {
        Write-Host "Unknown choice: $Choice (expected 1-$($Steps.Count) or 'all')"
        exit 1
    }
}
