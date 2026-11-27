param(
  [string]$ApiUrl = "http://localhost:8000",
  [string]$WebUrl = "http://localhost:3000",
  [int]$LoadPid = 0,
  [switch]$AllowRemoteTarget
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$compose = Join-Path $root "docker-compose.yml"
$results = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "results"
New-Item -ItemType Directory -Path $results -Force | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportPath = Join-Path $results "chaos-$stamp.json"
$resultados = @()
$ApiUrl = $ApiUrl.TrimEnd('/')
$WebUrl = $WebUrl.TrimEnd('/')
$HealthUrl = "$ApiUrl/health"

function Ahora { Get-Date -Format "yyyy-MM-ddTHH:mm:ssK" }

function Registrar([string]$nombre, [string]$estado, [string]$detalle) {
  $script:resultados += [ordered]@{
    escenario = $nombre
    estado = $estado
    detalle = $detalle
    fecha_hora = Ahora
  }
  Write-Output "[$estado] $nombre : $detalle"
}

function Compose([string[]]$accion) {
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = "SilentlyContinue"
  $salida = & docker compose --project-directory $root -f $compose @accion 2>&1 | Out-String
  $codigo = $LASTEXITCODE
  $ErrorActionPreference = $anterior
  Write-Output $salida
  if ($codigo -ne 0) { throw "docker compose $($accion -join ' ') falló con código $codigo" }
}

function Test-Url([string]$url) {
  try {
    $response = Invoke-WebRequest -Uri $url -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 400
  } catch {
    return $false
  }
}

function Esperar([bool]$esperado, [int]$timeoutSegundos) {
  $limite = (Get-Date).AddSeconds($timeoutSegundos)
  while ((Get-Date) -lt $limite) {
    if ((Test-Url $HealthUrl) -eq $esperado) { return $true }
    Start-Sleep -Seconds 2
  }
  return $false
}

function CargaActiva {
  if ($LoadPid -le 0) { return "sin prueba de carga" }
  try {
    $proceso = Get-Process -Id $LoadPid -ErrorAction Stop
    return "activa (PID $($proceso.Id))"
  } catch {
    return "PROCESO DE CARGA NO ACTIVO (PID $LoadPid)"
  }
}

if (-not ($ApiUrl -match '^https?://(localhost|127\.0\.0\.1)(:\d+)?/?$') -and -not $AllowRemoteTarget) {
  throw "Chaos está limitado a localhost. Use -AllowRemoteTarget solo con autorización explícita."
}

if (-not (Test-Url $HealthUrl)) {
  throw "La API no responde en $HealthUrl. Levante el stack antes de ejecutar chaos."
}

$pedido = $null
try {
  $body = @{
    customer_name = "Chaos-$stamp"
    items = @(@{ item_id = 1; quantity = 1 })
  } | ConvertTo-Json -Depth 5
  $pedido = Invoke-RestMethod -Method Post -Uri "$ApiUrl/orders" -Body $body -ContentType "application/json" -TimeoutSec 5
  Registrar "precondicion_pedido" "ok" "pedido_id=$($pedido.id) creado antes del caos; $(CargaActiva)"
} catch {
  throw "No se pudo crear el pedido de referencia: $_"
}

try {
  Compose @("stop", "api")
  if (Esperar $false 30) {
    Registrar "caida_api" "ok" "la API dejó de responder tras detener el contenedor api; $(CargaActiva)"
  } else {
    Registrar "caida_api" "fallo" "la API siguió respondiendo o no se pudo verificar la caída"
  }

  Compose @("start", "api")
  if (Esperar $true 90) {
    Registrar "recuperacion_api" "ok" "/health volvió a responder 2xx; $(CargaActiva)"
  } else {
    Registrar "recuperacion_api" "fallo" "/health no recuperó en 90 segundos"
  }

  try {
    $consultado = Invoke-RestMethod -Uri "$ApiUrl/orders/$($pedido.id)" -TimeoutSec 5
    if ($consultado.id -eq $pedido.id -and $consultado.customer_name -eq $pedido.customer_name) {
      Registrar "persistencia_pedidos" "ok" "pedido $($pedido.id) íntegro tras reinicio de api"
    } else {
      Registrar "persistencia_pedidos" "fallo" "el pedido recuperado no coincide con el original"
    }
  } catch {
    Registrar "persistencia_pedidos" "fallo" "no se pudo consultar el pedido: $_"
  }

  Compose @("restart", "api")
  if (Esperar $true 90) {
    Registrar "reinicio_api" "ok" "/health respondió tras docker compose restart api; $(CargaActiva)"
  } else {
    Registrar "reinicio_api" "fallo" "/health no respondió tras el reinicio"
  }

  Compose @("stop", "web")
  Start-Sleep -Seconds 3
  if (Test-Url $HealthUrl) {
    Registrar "perdida_nodo_web" "ok" "la API sigue disponible con el frontend detenido; $(CargaActiva)"
  } else {
    Registrar "perdida_nodo_web" "fallo" "la API dejó de estar disponible al detener web"
  }
  Compose @("start", "web")
  if (Test-Url $WebUrl) {
    Registrar "recuperacion_web" "ok" "frontend respondió en $WebUrl"
  } else {
    Registrar "recuperacion_web" "fallo" "frontend no respondió en $WebUrl"
  }

  $proxy = & docker ps --format "{{.Names}}" 2>&1 | Select-String -SimpleMatch "proxy"
  if ($proxy) {
    Registrar "reverse_proxy" "pendiente" "hay un contenedor proxy, pero su puerto/métricas dependen de Jesús; verificar manualmente"
  } else {
    Registrar "reverse_proxy" "pendiente" "no existe reverse proxy en el stack actual"
  }
} finally {
  Compose @("start", "api", "web")
  $recuperado = Esperar $true 90
  Registrar "recuperacion_final" $(if ($recuperado) { "ok" } else { "fallo" }) "estado final del stack local; $(CargaActiva)"
  $informe = [ordered]@{
    fecha_hora_inicio = $stamp
    fecha_hora_fin = Ahora
    objetivo = $ApiUrl
    pedido_referencia = $pedido.id
    criterios = "caída verificada, /health recuperado, pedido íntegro, frontend recuperado, sin borrado de volúmenes"
    escenarios = $resultados
  }
  $json = $informe | ConvertTo-Json -Depth 8
  [IO.File]::WriteAllText($reportPath, $json + [Environment]::NewLine, (New-Object Text.UTF8Encoding($false)))
  Write-Output "Informe: $reportPath"
}

if ($resultados | Where-Object { $_.estado -eq "fallo" }) { exit 1 }
exit 0
