# =============================================================================
#  Frame28 - instalador interactivo para Windows 10/11 (PowerShell 5.1 o 7)
#  A Think28 product - https://frame28.t28.io
#
#  Una sola linea, en Terminal de Windows o PowerShell:
#      irm https://frame28.t28.io/install.ps1 | iex
#
#  Pensado para un equipo recien instalado: usa winget (viene con Windows), acepta
#  sus acuerdos por ti, instala el runtime de Visual C++ si falta, y refresca el PATH
#  para no tener que abrir otra terminal. Te dice en que paso esta, por que, y te
#  pregunta antes de cada cosa. Es seguro repetirlo: lo que ya esta, lo salta.
#
#  Sin preguntas (para automatizar):   $env:FRAME28_YES=1; irm https://frame28.t28.io/install.ps1 | iex
#
#  Solo ASCII a proposito: Windows PowerShell 5.1 descarga la web en Latin-1.
# =============================================================================
& {  # todo en un bloque: con irm | iex, un exit cerraria la ventana de PowerShell del usuario y su mensaje (F28-101)
try {
$ErrorActionPreference = "Continue"
$Repo = "https://github.com/javierledesma28/frame28"
$Marketplace = "javierledesma28/frame28"
$Guide = "https://frame28.t28.io/presentacion/"
$Log = Join-Path $env:USERPROFILE "frame28-install.log"
$Yes = ($env:FRAME28_YES -eq "1")
$Total = 7
$script:Step = 0
"" | Out-File -FilePath $Log -Encoding utf8

function Say($t, $c = "White") { Write-Host $t -ForegroundColor $c; Add-Content -Path $Log -Value $t }
function Step($title, $why) { $script:Step++; Say ""; Say ("== Paso " + $script:Step + " de " + $Total + " - " + $title) "Yellow"; Say ("   " + $why) "DarkGray" }
function Ok($t)   { Say ("   OK  " + $t) "Green" }
function Skip($t) { Say ("   --  " + $t + " (ya estaba)") "DarkGray" }
function Warn($t) { Say ("   !   " + $t) "Yellow" }
function Fail($t) { Say ("   X   " + $t) "Red" }
function Has($n)  { $null -ne (Get-Command $n -ErrorAction SilentlyContinue) }
function Quit { throw "FRAME28_SALIR" }   # termina el instalador sin cerrar la terminal
function Node-Major { if (Has node) { $v = (node --version 2>$null) -replace '^v', ''; try { return [int]($v -split '\.')[0] } catch { return 0 } } return 0 }
function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
  $lb = Join-Path $env:USERPROFILE ".local\bin"; if (-not ($env:Path -split ";" | Where-Object { $_ -eq $lb })) { $env:Path = "$lb;$env:Path" }
}
function Ask($q) {  # devuelve $true = si
  if ($Yes) { return $true }
  $a = Read-Host ("   " + $q + " [S/n]")
  return -not ($a -match '^(n|no)$')
}
function Pause-Enter($q) { if (-not $Yes) { [void](Read-Host ("   " + $q + " (Enter para continuar)")) } }
function Retry-Or-Skip($what) {  # $true = reintentar, $false = saltar; sale si el usuario abandona
  Fail $what; Say ("   El detalle esta en " + $Log) "DarkGray"
  if ($Yes) { return $false }
  $a = Read-Host "   Reintentar (r), saltar este paso (s) o salir (q)? [r]"
  switch -Regex ($a) { '^(s|S)$' { return $false } '^(q|Q)$' { Say "   Cuando quieras, vuelve a ejecutar la misma linea. Hasta ahora."; Quit } default { return $true } }
}
function With-Retry($what, [scriptblock]$action) {  # ejecuta hasta que funcione o el usuario salte
  while ($true) {
    try { $out = & $action 2>&1; Add-Content -Path $Log -Value ($out | Out-String); if ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) { return $true } }
    catch { Add-Content -Path $Log -Value $_.Exception.Message }
    if (-not (Retry-Or-Skip $what)) { return $false }
  }
}
function Winget-Install($id) { winget install --id $id -e --accept-source-agreements --accept-package-agreements --silent --disable-interactivity; Refresh-Path }

# ---------- bienvenida ----------
$os = (Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue)
Say ""
Say "  +------------------------------------------------------+" "Yellow"
Say "  |   Frame28 - instalador                               |" "Yellow"
Say "  |   Graba hablando a camara. Frame28 monta el resto.   |" "Yellow"
Say "  |   A Think28 product - t28.io                         |" "Yellow"
Say "  +------------------------------------------------------+" "Yellow"
Say ""
if ($os) { Say ("  Sistema: " + $os.Caption + " (build " + $os.BuildNumber + ") - PowerShell " + $PSVersionTable.PSVersion) }
Say "  Voy a instalar, solo lo que falte:"
Say "    . ffmpeg (trabaja con el video)  . Node.js (motor de render)  . uv (instala Frame28)"
Say "    . runtime de Visual C++ (lo necesita el motor de audio)  . Claude Code  . el motor de Frame28  . el plugin"
Say "  Tiempo estimado: 5 minutos si ya tienes casi todo, 10-15 en un equipo recien instalado."
Say ("  Registro completo: " + $Log)
Say ""
Pause-Enter "Empezamos?"

# ---------- comprobaciones previas ----------
try { [void](Invoke-WebRequest -Uri "https://github.com" -UseBasicParsing -TimeoutSec 15) } catch { Fail "No hay conexion a internet (no llego a github.com). Conectate y vuelve a ejecutar la linea."; Quit }
if (-not (Has winget)) {
  Fail "No encuentro winget (viene con Windows 10 1809+ y Windows 11)."
  Say "   Abre la Microsoft Store, busca 'Instalador de aplicacion' (App Installer), instalalo o actualizalo, y vuelve a ejecutar la linea."
  Quit
}
# primera ejecucion de winget en un equipo nuevo: aceptar la fuente sin preguntar
winget source update --disable-interactivity 2>&1 | Out-Null

# ---------- 1) programas de apoyo ----------
Step "Programas de apoyo" "ffmpeg trabaja con el video, Node.js hace funcionar el motor de render, uv instala Frame28 con su propio Python y Git lo descarga de GitHub."
$pkgs = @(
  @{ cmd = "ffmpeg"; id = "Gyan.FFmpeg";       name = "ffmpeg" },
  @{ cmd = "node";   id = "OpenJS.NodeJS.LTS"; name = "Node.js" },
  @{ cmd = "uv";     id = "astral-sh.uv";      name = "uv" },
  @{ cmd = "git";    id = "Git.Git";           name = "Git" }   # uv lo necesita para instalar el motor desde git+https
)
foreach ($p in $pkgs) {
  if ($p.cmd -eq "node" -and (Has node) -and (Node-Major) -lt 22) {
    Say ("   Tienes Node.js " + (node --version) + "; el motor de render necesita la 22 o superior. Lo actualizo...")
    if (With-Retry "No se pudo actualizar Node.js con winget." { winget upgrade --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements --silent --disable-interactivity; if ($LASTEXITCODE -ne 0) { Winget-Install "OpenJS.NodeJS.LTS" }; Refresh-Path }) {
      if ((Node-Major) -ge 22) { Ok ("Node.js " + (node --version)) } else { Warn "Node.js sigue en una version antigua en esta terminal; abre una nueva y repite la linea." }
    }
    continue
  }
  if (Has $p.cmd) { Skip $p.name; continue }
  Say ("   Instalando " + $p.name + " (puede tardar unos minutos)...")
  $id = $p.id
  if (With-Retry ("No se pudo instalar " + $p.name + " con winget.") { Winget-Install $id }) {
    if (Has $p.cmd) { Ok $p.name } else { Warn ($p.name + " se instalo pero esta terminal aun no lo ve. Si algo falla mas adelante, abre una terminal nueva y repite la linea.") }
  }
}

# ---------- 2) runtime de Visual C++ ----------
Step "Runtime de Visual C++" "Un componente de Microsoft que necesitan el reconocimiento de voz y el recorte del hablante. En un Windows recien instalado suele faltar."
$vc = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" -ErrorAction SilentlyContinue
if ($vc -and $vc.Installed -eq 1) { Skip "Visual C++ 2015-2022 x64" }
else { if (With-Retry "No se pudo instalar el runtime de Visual C++." { Winget-Install "Microsoft.VCRedist.2015+.x64" }) { Ok "Visual C++ 2015-2022 x64" } }

# ---------- 3) Claude Code ----------
Step "Claude Code" "Es la aplicacion de Anthropic con la que hablaras para montar tus videos. Frame28 es un plugin suyo."
if (Has claude) { Skip ("Claude Code " + (claude --version 2>$null | Select-Object -First 1)) }
else {
  Say "   Instalo la version de terminal con el instalador oficial de Anthropic. Despues tendras que iniciar"
  Say "   sesion una vez con tu cuenta de Claude (plan Pro o superior). Si prefieres la app de escritorio,"
  Say "   tambien puedes descargarla de https://claude.com/claude-code; el plugin funciona igual."
  if (Ask "Instalo Claude Code (terminal)?") {
    if (With-Retry "No se pudo instalar Claude Code." { irm https://claude.ai/install.ps1 | iex; Refresh-Path }) {
      if (Has claude) { Ok "Claude Code instalado" } else { Warn "Claude Code se instalo pero no esta en esta terminal; abre una nueva mas tarde." }
    }
  } else { Skip "Claude Code (lo instalaras tu)" }
}

# ---------- 4) motor de Frame28 ----------
Step "Motor de Frame28" "El programa 'frame28' que transcribe, corta, recorta y renderiza. Se descarga de GitHub con uv (trae su propio Python)."
if (Has uv) {
  Say "   Descargando e instalando (1-3 minutos la primera vez)..."
  if (With-Retry "No se pudo instalar el motor de Frame28." { uv tool install --python 3.12 --force "git+$Repo#subdirectory=plugin/cli" }) {
    uv tool update-shell 2>&1 | Out-Null
    Refresh-Path
    if (Has frame28) { Ok ("frame28 " + ((frame28 --version) -split " ")[-1]) } else { Warn "frame28 quedo en %USERPROFILE%\.local\bin; abre una terminal nueva para usarlo." }
  }
} else { Fail "uv no esta disponible; no puedo instalar el motor. Abre una terminal nueva y vuelve a ejecutar la linea." }

# ---------- 5) plugin ----------
Step "Plugin de Frame28 en Claude Code" "Las instrucciones que convierten a Claude en director de montaje. Ocupan menos que una foto."
if (Has claude) {
  claude plugin marketplace add $Marketplace 2>&1 | Add-Content -Path $Log
  claude plugin marketplace update think28 2>&1 | Add-Content -Path $Log      # si ya estaba: trae la version publicada (F28-102)
  claude plugin install "frame28@think28" --scope user 2>&1 | Add-Content -Path $Log
  $installed = ($LASTEXITCODE -eq 0)
  claude plugin update "frame28@think28" 2>&1 | Add-Content -Path $Log
  if ($installed -or $LASTEXITCODE -eq 0) { Ok "Plugin frame28 instalado y al dia" }
  else {
    Warn "No pude instalarlo automaticamente (quiza falta iniciar sesion en Claude Code)."
    Say "   Cuando hayas iniciado sesion, escribe dentro de Claude Code:"
    Say ("      /plugin marketplace add " + $Marketplace); Say "      /plugin install frame28@think28"
  }
} else {
  Warn "Claude Code no esta disponible ahora. Cuando lo tengas, escribe dentro de Claude Code:"
  Say ("      /plugin marketplace add " + $Marketplace); Say "      /plugin install frame28@think28"
}

# ---------- 6) comprobacion ----------
Step "Comprobacion" "frame28 doctor revisa que cada pieza este en su sitio."
if (Has frame28) { frame28 doctor 2>&1 | Tee-Object -FilePath $Log -Append } else { Warn "frame28 no esta en esta terminal; abre una nueva y escribe: frame28 doctor" }

# ---------- 7) siguiente ----------
Step "Listo" "Que hacer ahora."
Say ""
Say "   Instalacion terminada. Cuatro cosas para empezar:" "Green"
Say "   1. Cierra esta terminal y abre una nueva (asi reconoce los programas nuevos)."
if (Has claude) { Say "   2. Escribe  claude  en la terminal e inicia sesion con tu cuenta de Claude (solo la primera vez)." } else { Say "   2. Instala Claude Code desde https://claude.com/claude-code e inicia sesion." }
Say "   3. Entra con tu cuenta de Frame28: dentro de Claude Code escribe  /mcp , elige frame28 y pulsa Authenticate."
Say "      Se abre el navegador: tu email y el codigo que te llega. Si no tienes cuenta, se crea gratis (modo demo)."
Say "   4. Graba un clip hablando a camara, abre Claude Code en su carpeta y escribe: `"Aqui esta mi clip. Montamelo.`""
Say ""
Say ("   Guia completa con imagenes: " + $Guide) "Yellow"
Say ("   Si algo fallo, envia el fichero " + $Log + " a quien te paso Frame28 o pegaselo a Claude.")
Say ""
} catch {
  if ($_.Exception.Message -ne "FRAME28_SALIR") { Write-Host ("   X   Error inesperado: " + $_.Exception.Message) -ForegroundColor Red; Write-Host "   Vuelve a ejecutar la linea; si se repite, envia el registro frame28-install.log de tu carpeta personal." }
}
}
