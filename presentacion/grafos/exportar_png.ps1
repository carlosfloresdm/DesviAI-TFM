# Exporta las vistas del grafo a PNG usando Microsoft Edge en modo headless.
# Uso (desde esta carpeta):   .\exportar_png.ps1            -> PNG 3840x2160 en .\png
#                            .\exportar_png.ps1 -Scale 1   -> PNG 1920x1080
param([int]$Scale = 2, [string]$OutDir = (Join-Path $PSScriptRoot 'png'))

$edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
          "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { throw 'No encontré Microsoft Edge instalado.' }

$html = (Join-Path $PSScriptRoot 'grafo-memorias.html') -replace '\\', '/'
New-Item -ItemType Directory -Force $OutDir | Out-Null
$perfil = Join-Path $env:TEMP 'edge-headless-desviai'

$red = (Join-Path $PSScriptRoot 'red-interactiva.html') -replace '\\', '/'
$vistas = @(
  @{ n = '1_una-obra-tres-memorias';        f = $html; q = 'view=narrativa' },
  @{ n = '2_red-completa';                  f = $html; q = 'view=red' },
  @{ n = '3a_agente_evidencia-directa';     f = $html; q = 'view=agente&scenario=directa' },
  @{ n = '3b_agente_evidencia-estadistica'; f = $html; q = 'view=agente&scenario=estadistica' },
  @{ n = '4a_red-obsidian';                 f = $red;  q = 'x=1' },
  @{ n = '4b_red-obsidian_obra-118';        f = $red;  q = 'select=obra-118' },
  @{ n = '4c_red-obsidian_hueco-normativa'; f = $red;  q = 'select=causa-normativa' }
)
foreach ($tema in 'dark', 'light') {
  $sufijo = if ($tema -eq 'dark') { 'oscuro' } else { 'claro' }
  foreach ($v in $vistas) {
    $out = Join-Path $OutDir "$($v.n)_$sufijo.png"
    & $edge --headless=new --disable-gpu --hide-scrollbars --user-data-dir="$perfil" `
      --window-size=1920,1080 --force-device-scale-factor=$Scale --virtual-time-budget=6000 `
      --screenshot="$out" "file:///$($v.f)`?$($v.q)&theme=$tema&export=1" 2>&1 | Out-Null
    Write-Output "OK  $out"
  }
}
