# run_nl.ps1 — Nederlandse leesbaarheidsanalyse, in één opdracht, op Windows.
#
#   .\nl\run_nl.ps1                            menu, vraagt om de map
#   .\nl\run_nl.ps1 rapport C:\pad\naar\tekst  meteen het volledige rapport
#   .\nl\run_nl.ps1 stijl   C:\pad\naar\tekst  alleen de stijlanalyse
#
# Installeert uv als het ontbreekt en laat uv Python, pakketten en het
# taalmodel regelen. De macOS/Linux-tegenhanger is run_nl.sh; houd ze gelijk.
#
# NOG NIET OP WINDOWS GETEST: geschreven en nagelopen naast run_nl.sh, maar alleen
# vanaf macOS gedraaid. Meld het gerust als er iets misgaat, met uw
# PowerShell-versie erbij ($PSVersionTable.PSVersion).

param(
    [string]$Opdracht = "",
    [string]$Map = "",
    [string]$Uitvoer = ""
)

$ErrorActionPreference = "Stop"

# PowerShell 7.2 maakt van alles wat een extern programma naar stderr schrijft een
# afbrekende fout zolang ErrorActionPreference op Stop staat, en uv meldt zijn
# voortgang daar. Wij kijken naar de afsluitcode, dus dit gaat uit waar het bestaat
# (7.3+ staat al op false; 5.1 kent de variabele niet).
if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

Set-Location (Join-Path $PSScriptRoot "..")

# --- 1. uv beschikbaar maken -------------------------------------------------
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv niet gevonden - wordt geïnstalleerd via astral.sh ..."
    # Windows PowerShell 5.1 gebruikt soms nog TLS 1.0; astral.sh weigert dat.
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "uv staat nog niet in het PATH. Open een nieuw PowerShell-venster en probeer opnieuw."
        exit 1
    }
}

# --- 2. omgeving klaarzetten -------------------------------------------------
# De groep 'nl' bevat spaCy, het Nederlandse taalmodel, pyphen en wordfreq.
# De eerste keer duurt dit even: er wordt ongeveer 100 MB opgehaald.
#
# --inexact is hier wezenlijk: zonder die vlag maakt `uv sync` de omgeving
# precies gelijk aan uv.lock en gooit het dus alles eruit wat daar niet in staat.
# De modellen md en lg worden met `uv pip install` opgehaald en staan niet in de
# lock, dus die werden bij de volgende start weer verwijderd — het model was dan
# "opgehaald" maar meteen weer weg.
Write-Host "Omgeving controleren ..."
uv sync --quiet --inexact --group nl
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Opdrachten = @("rapport", "leesbaarheid", "stijl", "dialoog", "woorden", "taalmodel")

if (-not $Opdracht) {
    Write-Host ""
    Write-Host "Nederlandse leesbaarheidsanalyse"
    Write-Host "--------------------------------"
    Write-Host "  1) rapport       volledig rapport (markdown + PDF + grafieken)"
    Write-Host "  2) leesbaarheid  Flesch-Douma en Leesindex A per hoofdstuk"
    Write-Host "  3) stijl         lijdende vorm, tangconstructies, schrapwoorden"
    Write-Host "  4) dialoog       dialoogaandeel, consistentie en tempo"
    Write-Host "  5) woorden       moeilijke woorden en woordvariatie"
    Write-Host "  6) taalmodel     nauwkeuriger taalmodel kiezen of installeren"
    Write-Host ""
    $keuze = Read-Host "Kies [1-6]"
    if ($keuze -match '^[1-6]$') {
        $Opdracht = $Opdrachten[[int]$keuze - 1]
    } else {
        Write-Host "Onbekende keuze: $keuze"
        exit 1
    }
}

# --- taalmodel: geen manuscriptmap nodig ------------------------------------
if ($Opdracht -eq "taalmodel") {
    if (-not $Map) {
        uv run --group nl python nl/analyseer.py taalmodel
        Write-Host ""
        $model = Read-Host "Welk model wilt u gebruiken? [sm/md/lg, leeg = laten staan]"
        if (-not $model) { exit 0 }
    } else {
        $model = $Map
    }

    uv run --group nl python nl/analyseer.py taalmodel $model
    if ($LASTEXITCODE -ne 0) { exit 1 }

    # Ophalen als het er nog niet is. `python -m spacy download` werkt hier niet:
    # dat roept pip aan, en een door uv beheerde omgeving heeft geen pip.
    # Eén regel Python, zodat PowerShell niets aan de aanhalingstekens verandert.
    $probe = "import sys; sys.path.insert(0, 'nl'); from leesbaarheid import taal; " +
             "naam = taal._volledige_naam('$model'); " +
             "print('' if taal.is_geinstalleerd(naam) else taal.MODELLEN[taal.MODEL_PER_NAAM[naam]].wheel)"
    $wheel = (uv run --group nl python -c $probe | Out-String).Trim()

    if ($wheel) {
        Write-Host ""
        $ja = Read-Host "Het model is nog niet geïnstalleerd. Nu ophalen? [J/n]"
        if (-not $ja) { $ja = "J" }
        if ($ja -match '^[JjYy]') {
            uv pip install $wheel
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        } else {
            Write-Host "Overgeslagen. Later zelf: uv pip install $wheel"
        }
    }
    exit 0
}

if (-not $Map) {
    Write-Host '(tip: klik in Verkenner met Shift+rechtermuisknop op de map -> "Als pad kopiëren" en plak het hier)'
    $Map = Read-Host "Map met uw .md- of .docx-bestanden"
}

# Een geplakt pad komt letterlijk binnen: de aanhalingstekens die "Als pad
# kopiëren" eromheen zet staan er nog, en ~ is nog door niets vervangen.
$Map = $Map.Trim()
if ($Map.Length -ge 2) {
    foreach ($q in @('"', "'")) {
        if ($Map.StartsWith($q) -and $Map.EndsWith($q)) {
            $Map = $Map.Substring(1, $Map.Length - 2)
        }
    }
}
if ($Map.StartsWith("~")) { $Map = $HOME + $Map.Substring(1) }
# Een afsluitende backslash weghalen, maar nooit bij een kale schijfletter:
# "C:\" wordt dan "C:", en dat betekent "waar ik het laatst was op C:".
if ($Map -notmatch '^[A-Za-z]:[\\/]?$') {
    $Map = $Map.TrimEnd([char[]]@('\', '/'))
}

if (-not (Test-Path -LiteralPath $Map -PathType Container)) {
    Write-Host ""
    Write-Host "Dit is geen map: $Map"
    Write-Host "Geef een bestaande map met .md- of .docx-bestanden, bijvoorbeeld:"
    Write-Host "  .\nl\run_nl.ps1 $Opdracht `"$env:USERPROFILE\Documenten\mijn-boek`""
    exit 1
}

Write-Host ""
# Een lege derde parameter niet doorgeven: argparse zou die als uitvoermap zien.
if ($Uitvoer) {
    uv run --group nl python nl/analyseer.py $Opdracht $Map $Uitvoer
} else {
    uv run --group nl python nl/analyseer.py $Opdracht $Map
}
exit $LASTEXITCODE
