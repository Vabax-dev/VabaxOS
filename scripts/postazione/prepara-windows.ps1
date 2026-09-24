<#
Prepares Windows 11 as the VabaxOS development workstation (ADR-0013).
Start it with 1-prepara-windows.cmd, which asks for administrator rights.
Every message is plain text, one line each, so it reads well with NVDA.
#>
#Requires -RunAsAdministrator

$ErrorActionPreference = 'Continue'
$env:WSL_UTF8 = '1'

$KitDir = $PSScriptRoot
$TargetDir = 'C:\VabaxOS-postazione'
$KitFiles = @('prepara-debian.sh', 'verifica-postazione.sh', 'pacchetti-debian.txt')
$script:Problems = 0

function Write-Step([string]$Text) { Write-Host ''; Write-Host "== $Text" }
function Write-Ok([string]$Text) { Write-Host "OK: $Text" }
function Write-Problem([string]$Text) { Write-Host "PROBLEMA: $Text"; $script:Problems++ }
function Test-Yes([string]$Question) {
    $answer = Read-Host "$Question Scrivi s per si, n per no, poi Invio"
    return ($answer -match '^[sSyY]')
}
function Install-WithWinget([string]$Id, [string]$Name) {
    winget list --exact --id $Id --accept-source-agreements *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "$Name è già installato."
        return
    }
    Write-Host "Installo $Name. Può volerci qualche minuto, aspetta il messaggio OK."
    winget install --exact --id $Id --source winget --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -eq 0) { Write-Ok "$Name installato." }
    else { Write-Problem "Installazione di $Name non riuscita, codice $LASTEXITCODE. Vedi la guida, sezione Problemi comuni." }
}

Write-Host 'Preparazione di Windows per lo sviluppo di VabaxOS.'
Write-Host 'Ogni domanda aspetta la tua risposta. Puoi rileggere tutto con i comandi di revisione di NVDA.'

Write-Step 'Passo 1 di 7: controlli del computer'
$os = Get-CimInstance Win32_OperatingSystem
$cs = Get-CimInstance Win32_ComputerSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$build = [int]$os.BuildNumber
if ($build -ge 22000) { Write-Ok "Windows 11, build $build." }
else { Write-Problem "Serve Windows 11. Questa è la build $build di Windows 10." }

$ramGB = [math]::Round($cs.TotalPhysicalMemory / 1GB)
if ($ramGB -ge 16) { Write-Ok "Memoria: $ramGB GB." }
elseif ($ramGB -ge 8) { Write-Host "AVVISO: memoria $ramGB GB. Basta, ma le costruzioni saranno lente. Ne consiglio 16." }
else { Write-Problem "Memoria: solo $ramGB GB. Ne servono almeno 8." }

$freeGB = [math]::Round((Get-PSDrive -Name C).Free / 1GB)
if ($freeGB -ge 60) { Write-Ok "Spazio libero sul disco C: $freeGB GB." }
else { Write-Problem "Spazio libero sul disco C: solo $freeGB GB. Ne servono almeno 60." }

if ($cs.HypervisorPresent -or $cpu.VirtualizationFirmwareEnabled) { Write-Ok 'Virtualizzazione attiva.' }
else { Write-Problem 'La virtualizzazione sembra spenta nel firmware del PC. Vedi la guida, sezione Problemi comuni.' }

$hasWinget = [bool](Get-Command winget -ErrorAction SilentlyContinue)
if ($hasWinget) { Write-Ok 'winget, il gestore dei programmi di Windows, è disponibile.' }
else { Write-Problem 'winget non è disponibile. Aggiorna Programma di installazione app dal Microsoft Store.' }

Write-Step 'Passo 2 di 7: programmi per Windows'
if ($hasWinget) {
    if (Get-AppxPackage -Name Microsoft.WindowsTerminal) { Write-Ok 'Windows Terminal è già installato.' }
    else { Install-WithWinget 'Microsoft.WindowsTerminal' 'Windows Terminal' }

    Write-Host 'Claude è l''app con cui lavorerai con me. Installandola accetti i suoi termini d''uso.'
    if (Test-Yes 'Installo l''app Claude?') { Install-WithWinget 'Anthropic.Claude' 'Claude' }

    Write-Host 'Visual Studio Code è un editor di codice. Non è indispensabile: serve solo se vuoi leggere o modificare i file da solo.'
    if (Test-Yes 'Installo Visual Studio Code?') { Install-WithWinget 'Microsoft.VisualStudioCode' 'Visual Studio Code' }
}

Write-Step 'Passo 3 di 7: WSL e Debian'
wsl.exe --update *> $null
$distros = @(wsl.exe --list --quiet 2>$null | ForEach-Object { ($_ -replace "`0", '').Trim() } | Where-Object { $_ })
if ($distros -contains 'Debian') {
    Write-Ok 'Debian è già installata in WSL.'
}
else {
    Write-Host 'Installo WSL e Debian. Può volerci qualche minuto.'
    wsl.exe --install --distribution Debian --no-launch
    if ($LASTEXITCODE -eq 0) { Write-Ok 'WSL e Debian installati.' }
    else { Write-Problem "Installazione di WSL non riuscita, codice $LASTEXITCODE." }
}
wsl.exe --set-default-version 2 *> $null

Write-Step 'Passo 4 di 7: configurazione di WSL'
$wslConfig = Join-Path $env:USERPROFILE '.wslconfig'
if (Test-Path $wslConfig) {
    Write-Host "AVVISO: il file $wslConfig esiste già e non lo modifico. Contiene:"
    Get-Content $wslConfig | ForEach-Object { Write-Host "  $_" }
    Write-Host 'Controlla che nella sezione [wsl2] ci sia nestedVirtualization=true.'
}
else {
    $lines = @('[wsl2]', 'nestedVirtualization=true')
    if ($ramGB -ge 30) { $lines += 'memory=16GB' }
    elseif ($ramGB -ge 15) { $lines += 'memory=10GB' }
    Set-Content -Path $wslConfig -Value $lines -Encoding ASCII
    Write-Ok "Creato $wslConfig con la virtualizzazione annidata attiva."
}

Write-Step 'Passo 5 di 7: copia degli script per Debian'
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
foreach ($file in $KitFiles) {
    $source = Join-Path $KitDir $file
    if (Test-Path $source) { Copy-Item -Path $source -Destination $TargetDir -Force }
    else { Write-Problem "Manca il file $file nella cartella da cui hai avviato lo script." }
}
Write-Ok "Script copiati in $TargetDir."

Write-Step 'Passo 6 di 7: sospensione durante le costruzioni'
Write-Host 'Costruire la ISO richiede anche mezz''ora. Se il PC va in sospensione, la costruzione si interrompe.'
if (Test-Yes 'Quando il PC è collegato alla corrente, disattivo la sospensione automatica?') {
    powercfg /change standby-timeout-ac 0
    Write-Ok 'Con il caricatore collegato il PC non va più in sospensione da solo. Con la batteria non cambia niente.'
}

Write-Step 'Passo 7 di 7: riepilogo'
if ($script:Problems -eq 0) { Write-Host 'Nessun problema trovato.' }
else { Write-Host "Problemi trovati: $($script:Problems). Rileggi le righe che iniziano con PROBLEMA." }
Write-Host 'Adesso serve un riavvio di Windows.'
Write-Host 'Dopo il riavvio apri Debian dal menu Start e segui la guida dalla parte 4.'
if (Test-Yes 'Riavvio Windows adesso?') { Restart-Computer }
else { Write-Host 'Riavvia quando vuoi. Puoi chiudere questa finestra.' }
