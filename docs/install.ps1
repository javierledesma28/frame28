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
$MotorGit = "git+$Repo@release#subdirectory=plugin/cli"   # la rama release: la ultima release publicada, no main (F28-91)
$GpuExcludes = "https://raw.githubusercontent.com/javierledesma28/frame28/release/plugin/cli/excluir-gpu.txt"
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
function App-Claude {  # el claude.exe de la app de escritorio (pestana Code), "" si no hay (F28-451)
  if ($env:CLAUDE_CODE_EXECPATH -and (Test-Path $env:CLAUDE_CODE_EXECPATH)) { return $env:CLAUDE_CODE_EXECPATH }
  $d = Join-Path $env:APPDATA "Claude\claude-code"   # <version>\<hash>\claude.exe: la version mas alta, no la ultima tocada
  $e = Get-ChildItem -Path (Join-Path $d "*\*\claude.exe") -ErrorAction SilentlyContinue |
       Sort-Object { try { [version]$_.Directory.Parent.Name } catch { [version]"0.0" } } -Descending | Select-Object -First 1
  if ($e) { return $e.FullName }
  return ""
}
function Motor-Version { if (Has frame28) { try { return ((frame28 --version 2>$null) -split " ")[-1] } catch { return "" } } return "" }
function Nvidia-Gpu {  # $true si hay una NVIDIA con su driver (nvidia-smi responde) (F28-452)
  if (-not (Has nvidia-smi)) { return $false }
  try { $null = & nvidia-smi -L 2>$null; return ($LASTEXITCODE -eq 0) } catch { return $false }
}
function Plugin-Version {  # version del plugin instalado en Claude Code, "" si no esta
  $f = Join-Path $env:USERPROFILE ".claude\plugins\installed_plugins.json"
  if (-not (Test-Path $f)) { return "" }
  try { $j = Get-Content $f -Raw | ConvertFrom-Json; $ps = $j.plugins; if (-not $ps) { $ps = $j }
        $e = $ps."frame28@think28"; if ($e) { return (@($e)[0]).version } } catch {}
  return ""
}
function Motor-Receipt {  # como esta instalado el motor segun uv (uv-receipt.toml), "" si no lo esta
  try { $d = uv tool dir 2>$null | Select-Object -First 1
        if ($d) { $f = Join-Path $d "frame28\uv-receipt.toml"; if (Test-Path $f) { return (Get-Content $f -Raw) } } } catch {}
  return ""
}
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
# Si Frame28 ya esta, el instalador es el actualizador: comprueba novedades y cambia solo lo necesario (F28-102)
Refresh-Path
$PrevMotor = Motor-Version; $PrevPlugin = Plugin-Version
$Update = ($PrevMotor -ne "" -or $PrevPlugin -ne "")
# sin claude en el PATH, la app de escritorio trae su propio claude.exe: con el basta, no hace falta la version de terminal (F28-451)
$Claude = "claude"; $App = $false
if (-not (Has claude)) { $a = App-Claude; if ($a) { $Claude = $a; $App = $true } }
$Reabrir = "abre una terminal nueva"; if ($App) { $Reabrir = "cierra la app de Claude del todo (tambien el icono junto al reloj) y vuelve a abrirla" }
$os = (Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue)
Say ""
Say "  +------------------------------------------------------+" "Yellow"
Say "  |   Frame28 - instalador                               |" "Yellow"
Say "  |   Graba hablando a camara. Frame28 monta el resto.   |" "Yellow"
Say "  |   A Think28 product - t28.io                         |" "Yellow"
Say "  +------------------------------------------------------+" "Yellow"
Say ""
if ($os) { Say ("  Sistema: " + $os.Caption + " (build " + $os.BuildNumber + ") - PowerShell " + $PSVersionTable.PSVersion) }
if ($Update) {
  $have = @(); if ($PrevMotor) { $have += ("motor " + $PrevMotor) }; if ($PrevPlugin) { $have += ("plugin " + $PrevPlugin) }
  Say ("  Ya tienes Frame28 en este ordenador (" + ($have -join ", ") + ").") "Green"
  Say "  Voy a comprobar si hay una version nueva y a actualizar solo lo que haga falta. No toco tus videos ni tu cuenta."
  Say "  Tiempo estimado: 1-2 minutos."
} else {
  Say "  Voy a instalar, solo lo que falte:"
  Say "    . ffmpeg (trabaja con el video)  . Node.js (motor de render)  . uv (instala Frame28)  . Git"
  Say "    . runtime de Visual C++ (lo necesita el motor de audio)  . Claude Code  . el motor de Frame28  . el plugin"
  Say "  Tiempo estimado: 10-15 minutos en un equipo recien instalado."
}
Say ("  Registro completo: " + $Log)
Say ""
if ($Update) { Pause-Enter "Compruebo?" } else { Pause-Enter "Empezamos?" }

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
      if ((Node-Major) -ge 22) { Ok ("Node.js " + (node --version)) } else { Warn ("Node.js sigue en una version antigua aqui; " + $Reabrir + " y repite la instalacion.") }
    }
    continue
  }
  if (Has $p.cmd) { Skip $p.name; continue }
  Say ("   Instalando " + $p.name + " (puede tardar unos minutos)...")
  $id = $p.id
  if (With-Retry ("No se pudo instalar " + $p.name + " con winget.") { Winget-Install $id }) {
    if (Has $p.cmd) { Ok $p.name } else { Warn ($p.name + " se instalo pero aqui aun no se ve. Si algo falla mas adelante, " + $Reabrir + " y repite la instalacion.") }
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
elseif ($App) { Ok "Uso el Claude Code de la app de escritorio; no instalo la version de terminal" }
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
  # Con las versiones exactas de las librerias con las que pasaron las pruebas (extra probado, F28-91), y el extra gpu si
  # ya lo tenia. Una instalacion anterior (sin esas versiones o de main) se reinstala; una de este instalador se actualiza.
  $rec = Motor-Receipt; $extras = "probado"; $gpuArgs = @()
  if ($rec -match '"gpu"') { $extras = "gpu,probado"; $gpuArgs = @("--excludes", $GpuExcludes) }
  $spec = "frame28[" + $extras + "] @ " + $MotorGit
  $upgrade = ($rec -match '"probado"') -and ($rec -match 'rev=release')
  # Con NVIDIA, la aceleracion por GPU (transcribir 4 veces mas rapido) es opcional y pesa: se avisa antes (F28-452)
  if (($extras -eq "probado") -and ($rec -notmatch 'editable') -and (Nvidia-Gpu)) {
    Say "   Tienes una tarjeta NVIDIA: puedo instalar tambien la aceleracion por GPU (transcribe unas 4 veces mas rapido)."
    Say "   Son unos 3,3 GB mas de descarga y disco. Sin ella todo funciona igual, por CPU."
    if (Ask "Instalo la aceleracion por GPU (unos 3,3 GB)?") {
      $extras = "gpu,probado"; $gpuArgs = @("--excludes", $GpuExcludes); $upgrade = $false
      $spec = "frame28[" + $extras + "] @ " + $MotorGit
    }
  }
  if ($rec -match 'editable') { Say "   --  el motor esta instalado en modo desarrollo (editable, desde un clon): no lo toco" "DarkGray" }
  else {
    if ($PrevMotor) { Say ("   Tienes el motor " + $PrevMotor + ". Busco la version publicada y, si es nueva, la instalo...") }
    else { Say "   Descargando e instalando (1-3 minutos la primera vez)..." }
    if (With-Retry "No se pudo instalar el motor de Frame28." { if ($upgrade) { uv tool upgrade frame28; if ($LASTEXITCODE -eq 0) { return } }; uv tool install --python 3.12 --force $spec @gpuArgs }) {
      uv tool update-shell 2>&1 | Out-Null
      Refresh-Path
      if (Has frame28) { Ok ("frame28 " + ((frame28 --version) -split " ")[-1]) } else { Warn ("frame28 quedo en %USERPROFILE%\.local\bin; " + $Reabrir + " para usarlo.") }
    }
  }
} else { Fail ("uv no esta disponible; no puedo instalar el motor. " + $Reabrir + " y vuelve a ejecutar la instalacion.") }

# ---------- 5) plugin ----------
Step "Plugin de Frame28 en Claude Code" "Las instrucciones que convierten a Claude en director de montaje. Ocupan menos que una foto."
# Plan B: pedirselo a Claude. /plugin no existe en la pestana Code de la app de escritorio (F28-451)
$PlanB = "      Instala el plugin de Frame28 siguiendo https://frame28.t28.io/instalar.md"
if ((Has claude) -or $App) {
  & $Claude plugin marketplace add $Marketplace 2>&1 | Add-Content -Path $Log
  & $Claude plugin marketplace update think28 2>&1 | Add-Content -Path $Log      # si ya estaba: trae la version publicada (F28-102)
  & $Claude plugin install "frame28@think28" --scope user 2>&1 | Add-Content -Path $Log
  $installed = ($LASTEXITCODE -eq 0)
  & $Claude plugin update "frame28@think28" 2>&1 | Add-Content -Path $Log
  if ($installed -or $LASTEXITCODE -eq 0) { Ok "Plugin frame28 instalado y al dia" }
  else {
    Warn "No pude instalarlo automaticamente (quiza falta iniciar sesion en Claude)."
    Say "   Cuando hayas iniciado sesion, abre una sesion de Claude Code (terminal o pestana Code de la app) y escribele:"
    Say $PlanB
  }
} else {
  Warn "Claude Code no esta disponible ahora. Cuando lo tengas, abre una sesion y escribele:"
  Say $PlanB
}

# ---------- 6) comprobacion ----------
Step "Comprobacion" "frame28 doctor revisa que cada pieza este en su sitio."
$F28 = Join-Path $env:USERPROFILE ".local\bin\frame28.exe"   # por su ruta: la app no ve el PATH nuevo hasta reiniciarse (F28-451)
if (Has frame28) { $F28 = "frame28" }
if ((Has frame28) -or (Test-Path $F28)) { & $F28 doctor 2>&1 | Tee-Object -FilePath $Log -Append } else { Warn ("frame28 no aparece; " + $Reabrir + " y pide a Claude: frame28 doctor") }

# ---------- 7) siguiente ----------
Step "Listo" "Que hacer ahora."
Say ""
if ($Update) {
  $NewMotor = Motor-Version; $NewPlugin = Plugin-Version
  $changes = @()
  if ($PrevMotor -and $NewMotor -and $NewMotor -ne $PrevMotor) { $changes += ("motor " + $PrevMotor + " -> " + $NewMotor) }
  if ($PrevPlugin -and $NewPlugin -and $NewPlugin -ne $PrevPlugin) { $changes += ("plugin " + $PrevPlugin + " -> " + $NewPlugin) }
  if (-not $PrevPlugin -and $NewPlugin) { $changes += ("plugin " + $NewPlugin + " (nuevo)") }
  if ($changes.Count -gt 0) {
    Say ("   Frame28 actualizado: " + ($changes -join ", ") + ".") "Green"
    if ($App) { Say "   Cierra la app de Claude del todo (tambien el icono junto al reloj) y vuelve a abrirla para usar la version nueva." }
    else { Say "   Cierra y vuelve a abrir Claude Code para usar la version nueva." }
  } else {
    Say ("   Todo estaba al dia (motor " + $NewMotor + ", plugin " + $NewPlugin + "). No he cambiado nada.") "Green"
  }
  Say "   Para trabajar: abre Claude Code en la carpeta de tu video y pidelo con tus palabras."
  Say ""
  Say ("   Guia completa con imagenes: " + $Guide) "Yellow"
  Say ("   Si algo fallo, envia el fichero " + $Log + " a quien te paso Frame28 o pegaselo a Claude.")
  Say ""
  Quit
}
if ($App) {  # solo la app de escritorio: sin terminal; la app toma el PATH nuevo al abrirse (F28-451)
  Say "   Instalacion terminada. Tres cosas para empezar:" "Green"
  Say "   1. Cierra la app de Claude del todo (tambien el icono junto al reloj) o reinicia el equipo:"
  Say "      asi reconoce los programas nuevos. Abrir solo una sesion nueva no basta."
  Say "   2. Entra con tu cuenta de Frame28 (una vez): en una sesion NUEVA de la pestana Code, escribe"
  Say "      `"Entra en mi cuenta de Frame28`". Se abre el navegador: tu email y el codigo que te llega."
  Say "   3. Graba un clip hablando a camara, abre otra sesion nueva en su carpeta y escribe: `"Aqui esta mi clip. Montamelo.`""
  Say ""
  Say ("   Guia completa con imagenes: " + $Guide) "Yellow"
  Say ("   Si algo fallo, envia el fichero " + $Log + " a quien te paso Frame28 o pegaselo a Claude.")
  Say ""
  Quit
}
Say "   Instalacion terminada. Cuatro cosas para empezar:" "Green"
Say "   1. Cierra esta terminal y abre una nueva (asi reconoce los programas nuevos)."
if (Has claude) { Say "   2. Escribe  claude  en la terminal e inicia sesion con tu cuenta de Claude (solo la primera vez)." } else { Say "   2. Instala Claude Code desde https://claude.com/claude-code e inicia sesion." }
Say "   3. Entra con tu cuenta de Frame28 (una vez): en la terminal nueva escribe  claude mcp login plugin:frame28:frame28"
Say "      Se abre el navegador: tu email y el codigo que te llega. Si no tienes cuenta, se crea gratis (modo demo)."
Say "      Si dice que no conoce 'login', escribe antes  claude update  (o dentro de claude: /mcp, frame28, Authenticate)."
Say "   4. Graba un clip hablando a camara, abre una sesion NUEVA de Claude Code (terminal o app de escritorio) en su carpeta"
Say "      y escribe: `"Aqui esta mi clip. Montamelo.`" (Frame28 sale en las sesiones que empiezan despues de entrar.)"
Say ""
Say ("   Guia completa con imagenes: " + $Guide) "Yellow"
Say ("   Si algo fallo, envia el fichero " + $Log + " a quien te paso Frame28 o pegaselo a Claude.")
Say ""
} catch {
  if ($_.Exception.Message -ne "FRAME28_SALIR") { Write-Host ("   X   Error inesperado: " + $_.Exception.Message) -ForegroundColor Red; Write-Host "   Vuelve a ejecutar la linea; si se repite, envia el registro frame28-install.log de tu carpeta personal." }
}
}
