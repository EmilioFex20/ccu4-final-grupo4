param(
  [string]$TargetHost = "http://localhost:8000",
  [int]$NormalUsers = 10,
  [int]$PeakUsers = 100,
  [int]$SpikeUsers = 150,
  [int]$RampRate = 10,
  [int]$DurationNormal = 30,
  [int]$DurationRamp = 60,
  [int]$DurationSpike = 30,
  [int]$DurationSustained = 60,
  [int]$DurationRampDown = 60,
  [int]$DurationRecovery = 30,
  [switch]$AllowRemoteTarget
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $root ".venv"
$requirements = Join-Path $root "requirements.txt"
$results = Join-Path $root "results"
$locustfile = Join-Path $root "locustfile.py"

if (-not (Test-Path -LiteralPath $venv)) {
  python -m venv $venv
}
$python = Join-Path $venv "Scripts/python.exe"
& $python -m pip install --disable-pip-version-check -r $requirements
if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias de Locust" }

$env:TARGET_HOST = $TargetHost
$env:NORMAL_USERS = "$NormalUsers"
$env:PEAK_USERS = "$PeakUsers"
$env:SPIKE_USERS = "$SpikeUsers"
$env:RAMP_RATE = "$RampRate"
$env:DURATION_NORMAL = "$DurationNormal"
$env:DURATION_RAMP = "$DurationRamp"
$env:DURATION_SPIKE = "$DurationSpike"
$env:DURATION_SUSTAINED = "$DurationSustained"
$env:DURATION_RAMPDOWN = "$DurationRampDown"
$env:DURATION_RECOVERY = "$DurationRecovery"
if ($AllowRemoteTarget) {
  $env:ALLOW_REMOTE_TARGET = "1"
} else {
  Remove-Item Env:ALLOW_REMOTE_TARGET -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Path $results -Force | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$prefix = Join-Path $results "locust-$stamp"
$locust = Join-Path $venv "Scripts/locust.exe"

Write-Output "Objetivo: $TargetHost | inicio: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')"
& $locust -f $locustfile --host $TargetHost --headless --csv $prefix --html "$prefix-report.html" --loglevel INFO
$code = $LASTEXITCODE
Write-Output "Fin: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK') | codigo: $code"
Write-Output "Resultados: $prefix*.csv y $prefix-report.html | fases: $(Join-Path $results 'fases.log')"
exit $code
