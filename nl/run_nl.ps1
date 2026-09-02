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
# --inexact: een sync maakt de omgeving precies gelijk aan de genoemde groepen.
# De grotere modellen md en lg staan in hun eigen groep (nl-md, nl-lg), dus
# zonder deze vlag zou elke start het gekozen model weer verwijderen.
Write-Host "Omgeving controleren ..."
uv sync --quiet --inexact --group nl
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Eén lijst: naam en omschrijving samen, zodat het menu en wat er draait niet
# uit elkaar kunnen lopen.
$Opdrachten = @(
    @{ naam = "rapport";      uitleg = "volledig rapport (markdown + PDF + grafieken)" }
    @{ naam = "leesbaarheid"; uitleg = "Flesch-Douma en Leesindex A per hoofdstuk" }
    @{ naam = "stijl";        uitleg = "lijdende vorm, tangconstructies, schrapwoorden" }
    @{ naam = "dialoog";      uitleg = "dialoogaandeel, consistentie en tempo" }
    @{ naam = "woorden";      uitleg = "moeilijke woorden en woordvariatie" }
    @{ naam = "taalmodel";    uitleg = "nauwkeuriger taalmodel kiezen of installeren" }
)

if (-not $Opdracht) {
    Write-Host ""
    Write-Host "Nederlandse leesbaarheidsanalyse"
    Write-Host "--------------------------------"
    for ($i = 0; $i -lt $Opdrachten.Count; $i++) {
        Write-Host ("  {0}) {1,-13} {2}" -f ($i + 1), $Opdrachten[$i].naam, $Opdrachten[$i].uitleg)
    }
    Write-Host ""
    $keuze = Read-Host "Kies [1-$($Opdrachten.Count)]"
    $nummer = 0
    if ([int]::TryParse($keuze, [ref]$nummer) -and $nummer -ge 1 -and $nummer -le $Opdrachten.Count) {
        $Opdracht = $Opdrachten[$nummer - 1].naam
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

    # --installeer haalt het model op als het er nog niet is. Welke groep
    # daarvoor nodig is weet analyseer.py; dit script hoeft dat niet te weten.
    uv run --group nl python nl/analyseer.py taalmodel $model --installeer
    exit $LASTEXITCODE
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
