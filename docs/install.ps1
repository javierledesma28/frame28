# Frame28 - instalador para Windows (PowerShell 5.1 o 7). Solo ASCII: Windows PowerShell 5.1 lee la web en Latin-1.
# Uso (una sola linea, en una Terminal de Windows):
#   irm https://frame28.t28.io/install.ps1 | iex
#
# Que hace, en orden, y solo lo que falte:
#   1. ffmpeg, Node.js LTS y uv con winget (el gestor de paquetes que trae Windows 10/11)
#   2. El motor de Frame28 (CLI `frame28`) con uv, desde GitHub
#   3. El plugin de Claude Code, si `claude` esta instalado
#   4. `frame28 doctor` para comprobar que todo esta en su sitio
# Es seguro ejecutarlo varias veces: si algo ya esta, lo salta.

$ErrorActionPreference = "Stop"
$Repo = "https://github.com/javierledesma28/frame28"
$Marketplace = "javierledesma28/frame28"

function Write-Step($t) { Write-Host ""; Write-Host "==> $t" -ForegroundColor Yellow }
function Write-Ok($t)   { Write-Host "    OK  $t" -ForegroundColor Green }
function Write-Skip($t) { Write-Host "    --  $t" -ForegroundColor DarkGray }
function Test-Cmd($n)   { $null -ne (Get-Command $n -ErrorAction SilentlyContinue) }
function Refresh-Path   { $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User") }

Write-Host ""
Write-Host "  Frame28 - A Think28 product - instalador para Windows" -ForegroundColor Yellow
Write-Host "  Graba hablando a camara. Frame28 monta el resto."
Write-Host ""

if (-not (Test-Cmd winget)) {
  Write-Host "No encuentro winget. Instala 'Instalador de aplicacion' desde la Microsoft Store y vuelve a ejecutar esto." -ForegroundColor Red
  exit 1
}

# 1) programas de apoyo
$pkgs = @(
  @{ cmd = "ffmpeg"; id = "Gyan.FFmpeg";        name = "ffmpeg (trabaja con el video)" },
  @{ cmd = "node";   id = "OpenJS.NodeJS.LTS";  name = "Node.js (motor de render)" },
  @{ cmd = "uv";     id = "astral-sh.uv";       name = "uv (instala Frame28)" }
)
foreach ($p in $pkgs) {
  Write-Step $p.name
  if (Test-Cmd $p.cmd) { Write-Skip "ya instalado"; continue }
  winget install --id $p.id -e --accept-source-agreements --accept-package-agreements --silent | Out-Null
  Refresh-Path
  if (Test-Cmd $p.cmd) { Write-Ok "instalado" } else { Write-Host "    Instalado, pero hace falta abrir una terminal nueva para que se reconozca. Abrela y vuelve a ejecutar la misma linea." -ForegroundColor Red; exit 1 }
}

# 2) el motor de Frame28
Write-Step "Motor de Frame28 (frame28)"
uv tool install --python 3.12 --force "git+$Repo#subdirectory=plugin/cli" | Out-Null
uv tool update-shell | Out-Null
$localBin = Join-Path $env:USERPROFILE ".local\bin"
if (-not ($env:Path -split ";" | Where-Object { $_ -eq $localBin })) { $env:Path = "$localBin;$env:Path" }
if (Test-Cmd frame28) { Write-Ok ("frame28 " + (frame28 --version)) } else { Write-Host "    frame28 no aparece en el PATH: abre una terminal nueva y escribe 'frame28 doctor'." -ForegroundColor Red }

# 3) el plugin de Claude Code
Write-Step "Plugin de Claude Code"
if (Test-Cmd claude) {
  try { claude plugin marketplace add $Marketplace 2>&1 | Out-Null } catch {}
  try { claude plugin install "frame28@think28" --scope user 2>&1 | Out-Null; Write-Ok "frame28@think28 instalado (reinicia Claude Code para que lo cargue)" } catch { Write-Host "    No pude instalar el plugin automaticamente. En Claude Code escribe: /plugin marketplace add $Marketplace  y luego  /plugin install frame28@think28" -ForegroundColor Red }
} else {
  Write-Skip "Claude Code no esta instalado o no esta en el PATH. Descargalo de https://claude.com/claude-code y luego, dentro de Claude Code, escribe:"
  Write-Host "        /plugin marketplace add $Marketplace"
  Write-Host "        /plugin install frame28@think28"
}

# 4) comprobacion
Write-Step "Comprobacion final"
if (Test-Cmd frame28) { frame28 doctor }
Write-Host ""
Write-Host "  Listo. Guia de uso: https://frame28.t28.io/presentacion/" -ForegroundColor Yellow
Write-Host ""
