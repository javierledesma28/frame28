#!/bin/bash
# =============================================================================
#  Frame28 · instalador interactivo para macOS (y Linux Debian/Ubuntu)
#  A Think28 product · https://frame28.t28.io
#
#  Una sola línea, en Terminal:
#      curl -fsSL https://frame28.t28.io/install.sh | bash
#
#  Pensado para un equipo recién instalado: si no hay Homebrew lo instala,
#  si Homebrew pide las Command Line Tools de Xcode o la contraseña, avisa antes.
#  Te dice en qué paso está, por qué, y te pregunta antes de cada cosa.
#  Es seguro repetirlo: lo que ya está, lo salta.
#
#  Sin preguntas (para automatizar):   curl -fsSL https://frame28.t28.io/install.sh | bash -s -- -y
# =============================================================================
set -u

# ---------- ajustes ----------
REPO="https://github.com/javierledesma28/frame28"
MARKET="javierledesma28/frame28"
GUIDE="https://frame28.t28.io/presentacion/"
LOG="$HOME/frame28-install.log"
YES=0
for a in "$@"; do [ "$a" = "-y" ] || [ "$a" = "--yes" ] && YES=1; done
[ "${FRAME28_YES:-0}" = "1" ] && YES=1

# ---------- colores y helpers ----------
if [ -t 1 ] || [ -e /dev/tty ]; then Y='\033[1;33m'; G='\033[32m'; R='\033[31m'; D='\033[90m'; B='\033[1m'; N='\033[0m'; else Y=''; G=''; R=''; D=''; B=''; N=''; fi
say()   { printf "%b\n" "$1"; printf "%s\n" "$(printf "%b" "$1" | sed 's/\x1b\[[0-9;]*m//g')" >> "$LOG"; }
step()  { say "\n${Y}══ Paso $1 de $TOTAL · $2${N}"; say "${D}   $3${N}"; }
ok()    { say "   ${G}✓ $1${N}"; }
skip()  { say "   ${D}– $1 (ya estaba)${N}"; }
warn()  { say "   ${Y}! $1${N}"; }
fail()  { say "   ${R}✗ $1${N}"; }
has()   { command -v "$1" >/dev/null 2>&1; }
motor_version() { has frame28 && frame28 --version 2>/dev/null | awk '{print $NF}' || true; }
plugin_version() {  # versión del plugin instalado en Claude Code, vacío si no está
  f="$HOME/.claude/plugins/installed_plugins.json"; [ -f "$f" ] || return 0
  sed -n '/"frame28@think28"/,/]/p' "$f" | sed -n 's/.*"version": *"\([^"]*\)".*/\1/p' | head -1
}
node_major() { has node && node --version 2>/dev/null | sed 's/^v//; s/\..*//' || echo 0; }
run()   { "$@" >> "$LOG" 2>&1; }

# Leer del teclado aunque el script llegue por una tubería (curl | bash)
ask() {  # ask "pregunta" → 0 = sí
  if [ "$YES" = "1" ]; then return 0; fi
  printf "%b" "   ${B}$1${N} [S/n] "
  if [ -e /dev/tty ]; then read -r ans < /dev/tty; else read -r ans; fi
  case "${ans:-s}" in n|N|no|NO) return 1 ;; *) return 0 ;; esac
}
pause() {
  if [ "$YES" = "1" ]; then return 0; fi
  printf "%b" "   ${B}$1${N} (Enter para continuar) "
  if [ -e /dev/tty ]; then read -r _ < /dev/tty; else read -r _; fi
}
retry_or_skip() {  # retry_or_skip "qué falló" → 0 = reintentar, 1 = saltar, sale si el usuario abandona
  fail "$1"
  say "   ${D}El detalle está en $LOG${N}"
  if [ "$YES" = "1" ]; then return 1; fi
  printf "%b" "   ${B}¿Reintentar (r), saltar este paso (s) o salir (q)?${N} [r] "
  if [ -e /dev/tty ]; then read -r ans < /dev/tty; else read -r ans; fi
  case "${ans:-r}" in s|S) return 1 ;; q|Q) say "\n   Cuando quieras, vuelve a ejecutar la misma línea. Hasta ahora."; exit 1 ;; *) return 0 ;; esac
}
with_retry() {  # with_retry "mensaje de fallo" comando args...  (reintenta hasta que funcione o el usuario salte)
  local msg="$1"; shift
  while true; do
    if "$@" >> "$LOG" 2>&1; then return 0; fi
    retry_or_skip "$msg" || return 1
  done
}

# ---------- bienvenida ----------
: > "$LOG"
# Si Frame28 ya está, el instalador es el actualizador: comprueba novedades y cambia solo lo necesario (F28-102)
export PATH="$HOME/.local/bin:$PATH"
PREV_MOTOR=$(motor_version); PREV_PLUGIN=$(plugin_version)
UPDATE=0; { [ -n "$PREV_MOTOR" ] || [ -n "$PREV_PLUGIN" ]; } && UPDATE=1
OS=$(uname -s); ARCH=$(uname -m)
say ""
say "${Y}  ┌──────────────────────────────────────────────────────┐${N}"
say "${Y}  │   Frame28 · instalador                               │${N}"
say "${Y}  │   Graba hablando a cámara. Frame28 monta el resto.   │${N}"
say "${Y}  │   A Think28 product · t28.io                         │${N}"
say "${Y}  └──────────────────────────────────────────────────────┘${N}"
say ""
if [ "$OS" = "Darwin" ]; then
  MACV=$(sw_vers -productVersion 2>/dev/null || echo "?")
  say "  Sistema: macOS $MACV ($ARCH)"
  TOTAL=7
else
  say "  Sistema: $(uname -sr) ($ARCH)"
  TOTAL=6
fi
if [ "$UPDATE" = "1" ]; then
  HAVE=""; [ -n "$PREV_MOTOR" ] && HAVE="motor $PREV_MOTOR"; [ -n "$PREV_PLUGIN" ] && HAVE="${HAVE:+$HAVE, }plugin $PREV_PLUGIN"
  say "  ${G}Ya tienes Frame28 en este ordenador ($HAVE).${N}"
  say "  Voy a comprobar si hay una versión nueva y a actualizar solo lo que haga falta. No toco tus vídeos ni tu cuenta."
  say "  Tiempo estimado: 1–2 minutos."
else
  say "  Voy a instalar, solo lo que falte:"
  if [ "$OS" = "Darwin" ]; then say "    1. Homebrew (el instalador de programas del Mac)"; fi
  say "    · ffmpeg (trabaja con el video)  · Node.js (motor de render)  · uv (instala Frame28)  · Git"
  say "    · Claude Code (la app que dirige el montaje)  · el motor de Frame28  · el plugin"
  say "  Tiempo estimado: 15–20 minutos en un equipo recién instalado."
fi
say "  Registro completo: $LOG"
say ""
if [ "$YES" != "1" ]; then if [ "$UPDATE" = "1" ]; then pause "¿Compruebo?"; else pause "¿Empezamos?"; fi; fi

# ---------- comprobaciones previas ----------
if ! curl -fsS --max-time 15 https://github.com >/dev/null 2>&1; then
  fail "No hay conexión a internet (no llego a github.com). Conéctate y vuelve a ejecutar la línea."; exit 1
fi
if [ "$OS" = "Darwin" ]; then
  MAJOR=${MACV%%.*}
  if [ "${MAJOR:-0}" -lt 12 ] 2>/dev/null; then
    warn "Tu macOS ($MACV) es antiguo: Homebrew necesita macOS 12 o superior. Puede que algo falle; sigo, pero si algo no va, actualiza el sistema."
  fi
fi

STEP=0

# ---------- 1) Homebrew (solo Mac) ----------
if [ "$OS" = "Darwin" ]; then
  STEP=$((STEP+1)); step $STEP "Homebrew" "Es el instalador de programas del Mac. Sin él, lo demás no se puede instalar."
  # cargar brew si existe pero no está en el PATH (Mac nuevo, terminal sin reiniciar)
  for bp in /opt/homebrew/bin/brew /usr/local/bin/brew; do [ -x "$bp" ] && eval "$($bp shellenv)"; done
  if has brew; then
    skip "Homebrew $(brew --version 2>/dev/null | head -1 | awk '{print $2}')"
  else
    say "   Homebrew lo instala Apple-style: te pedirá la ${B}contraseña de tu Mac${N} (no se ve al escribir) y que"
    say "   pulses ${B}Enter${N} para confirmar. Si tampoco tienes las 'Command Line Tools' de Xcode, las descargará"
    say "   él mismo: eso tarda ${B}5–15 minutos${N} y es normal que parezca que no pasa nada."
    if ask "¿Instalo Homebrew ahora?"; then
      # el instalador de Homebrew es interactivo: necesita el teclado
      if [ -e /dev/tty ]; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" < /dev/tty 2>&1 | tee -a "$LOG"
      else
        NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" 2>&1 | tee -a "$LOG"
      fi
      for bp in /opt/homebrew/bin/brew /usr/local/bin/brew; do [ -x "$bp" ] && eval "$($bp shellenv)"; done
      if has brew; then
        ok "Homebrew instalado"
        # dejarlo cargado en las próximas terminales
        ZP="$HOME/.zprofile"; touch "$ZP"
        grep -q "brew shellenv" "$ZP" 2>/dev/null || echo "eval \"\$($(command -v brew) shellenv)\"" >> "$ZP"
      else
        fail "Homebrew no quedó instalado. Abre https://brew.sh, sigue su línea de instalación y vuelve a ejecutar este instalador."; exit 1
      fi
    else
      fail "Sin Homebrew no puedo continuar en Mac."; exit 1
    fi
  fi
fi

# ---------- 2) programas de apoyo ----------
STEP=$((STEP+1)); step $STEP "Programas de apoyo" "ffmpeg trabaja con el video, Node.js hace funcionar el motor de render, uv instala Frame28 con su propio Python y Git lo descarga de GitHub."
if [ "$OS" = "Darwin" ]; then
  for pair in "ffmpeg:ffmpeg" "node:node" "uv:uv" "git:git"; do   # git suele venir con las herramientas de Apple que pide Homebrew
    cmd=${pair%%:*}; pkg=${pair##*:}
    if [ "$cmd" = "node" ] && has node && [ "$(node_major)" -lt 22 ] 2>/dev/null; then
      say "   Tienes Node.js $(node --version); el motor de render necesita la 22 o superior. Lo actualizo con Homebrew…"
      with_retry "No se pudo actualizar Node.js con Homebrew." bash -c "brew upgrade node || brew install node" && ok "node $(node --version 2>/dev/null)"
      continue
    fi
    if has "$cmd"; then skip "$pkg"; continue; fi
    say "   Instalando $pkg con Homebrew (puede tardar unos minutos)…"
    if with_retry "No se pudo instalar $pkg con Homebrew." brew install "$pkg"; then ok "$pkg"; fi
  done
else
  if ! has apt-get; then
    fail "Este instalador sabe instalar en Debian y Ubuntu (apt). En otra distribución instala ffmpeg, Node.js 22+, Git y uv con su gestor y vuelve a ejecutar la línea."; exit 1
  fi
  if ! has ffmpeg || ! has git || ! has node; then say "   Actualizando la lista de paquetes (pedirá tu contraseña para sudo)…"; with_retry "No se pudo actualizar la lista de paquetes." sudo apt-get update; fi
  if has node && [ "$(node_major)" -lt 22 ] 2>/dev/null; then say "   Tienes Node.js $(node --version); hace falta la 22 o superior. Lo actualizo…"; with_retry "No se pudo actualizar Node.js." bash -c "curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs" && ok "node $(node --version 2>/dev/null)"; fi
  if ! has ffmpeg; then say "   Instalando ffmpeg (pedirá tu contraseña para sudo)…"; with_retry "No se pudo instalar ffmpeg." sudo apt-get install -y ffmpeg && ok "ffmpeg"; else skip "ffmpeg"; fi
  if ! has node; then say "   Instalando Node.js 22…"; with_retry "No se pudo instalar Node.js." bash -c "curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs" && ok "node"; else skip "node"; fi
  if ! has git; then say "   Instalando Git…"; with_retry "No se pudo instalar Git." sudo apt-get install -y git && ok "git"; else skip "git"; fi
  if ! has uv; then say "   Instalando uv…"; with_retry "No se pudo instalar uv." bash -c "curl -LsSf https://astral.sh/uv/install.sh | sh" && ok "uv"; else skip "uv"; fi
fi
export PATH="$HOME/.local/bin:$PATH"
for cmd in ffmpeg node uv git; do has "$cmd" || warn "$cmd no está disponible en esta terminal. Si el paso anterior lo instaló, abre una Terminal nueva y vuelve a ejecutar la línea."; done

# ---------- 3) Claude Code ----------
STEP=$((STEP+1)); step $STEP "Claude Code" "Es la aplicación de Anthropic con la que hablarás para montar tus videos. Frame28 es un plugin suyo."
if has claude; then
  skip "Claude Code $(claude --version 2>/dev/null | head -1)"
else
  say "   Instalo la versión de terminal con el instalador oficial de Anthropic. Después tendrás que iniciar"
  say "   sesión una vez con tu cuenta de Claude (plan Pro o superior). Si prefieres la app de escritorio,"
  say "   también puedes descargarla de https://claude.com/claude-code; el plugin funciona igual."
  if ask "¿Instalo Claude Code (terminal)?"; then
    if with_retry "No se pudo instalar Claude Code." bash -c "curl -fsSL https://claude.ai/install.sh | bash"; then
      export PATH="$HOME/.local/bin:$PATH"
      has claude && ok "Claude Code instalado" || warn "Claude Code se instaló pero no está en esta terminal; abre una nueva más tarde."
    fi
  else
    skip "Claude Code (lo instalarás tú)"
  fi
fi

# ---------- 4) motor de Frame28 ----------
STEP=$((STEP+1)); step $STEP "Motor de Frame28" "El programa 'frame28' que transcribe, corta, recorta y renderiza. Se descarga de GitHub con uv (trae su propio Python)."
if has uv; then
  if [ -n "$PREV_MOTOR" ]; then say "   Tienes el motor $PREV_MOTOR. Busco la versión publicada y, si es nueva, la instalo…"
  else say "   Descargando e instalando (1–3 minutos la primera vez)…"; fi
  if [ -n "$PREV_MOTOR" ]; then MOTOR_CMD="uv tool upgrade frame28 || uv tool install --python 3.12 --force 'git+$REPO#subdirectory=plugin/cli'"
  else MOTOR_CMD="uv tool install --python 3.12 --force 'git+$REPO#subdirectory=plugin/cli'"; fi
  if with_retry "No se pudo instalar el motor de Frame28." bash -c "$MOTOR_CMD"; then
    run uv tool update-shell || true
    export PATH="$HOME/.local/bin:$PATH"
    has frame28 && ok "frame28 $(frame28 --version 2>/dev/null | awk '{print $NF}')" || warn "frame28 quedó instalado en ~/.local/bin; abre una Terminal nueva para usarlo."
  fi
else
  fail "uv no está disponible; no puedo instalar el motor. Abre una Terminal nueva y vuelve a ejecutar la línea."
fi

# ---------- 5) plugin de Claude Code ----------
STEP=$((STEP+1)); step $STEP "Plugin de Frame28 en Claude Code" "Las instrucciones que convierten a Claude en director de montaje. Ocupan menos que una foto."
if has claude; then
  run claude plugin marketplace add "$MARKET" || true
  run claude plugin marketplace update think28 || true          # si ya estaba: trae la versión publicada (F28-102)
  installed=1; run claude plugin install "frame28@think28" --scope user || installed=0
  run claude plugin update "frame28@think28" && installed=1 || true
  if [ "$installed" = "1" ]; then
    ok "Plugin frame28 instalado y al día"
  else
    warn "No pude instalarlo automáticamente (quizá falta iniciar sesión en Claude Code)."
    say "   Cuando hayas iniciado sesión, escribe dentro de Claude Code:"
    say "      /plugin marketplace add $MARKET"
    say "      /plugin install frame28@think28"
  fi
else
  warn "Claude Code no está disponible ahora. Cuando lo tengas, escribe dentro de Claude Code:"
  say "      /plugin marketplace add $MARKET"
  say "      /plugin install frame28@think28"
fi

# ---------- 6) comprobación ----------
STEP=$((STEP+1)); step $STEP "Comprobación" "frame28 doctor revisa que cada pieza esté en su sitio."
if has frame28; then frame28 doctor 2>&1 | tee -a "$LOG"; else warn "frame28 no está en esta terminal; abre una nueva y escribe: frame28 doctor"; fi

# ---------- 7) siguiente ----------
STEP=$((STEP+1)); step $STEP "Listo" "Qué hacer ahora."
say ""
if [ "$UPDATE" = "1" ]; then
  NEW_MOTOR=$(motor_version); NEW_PLUGIN=$(plugin_version); CHANGES=""
  [ -n "$PREV_MOTOR" ] && [ -n "$NEW_MOTOR" ] && [ "$NEW_MOTOR" != "$PREV_MOTOR" ] && CHANGES="motor $PREV_MOTOR → $NEW_MOTOR"
  [ -n "$PREV_PLUGIN" ] && [ -n "$NEW_PLUGIN" ] && [ "$NEW_PLUGIN" != "$PREV_PLUGIN" ] && CHANGES="${CHANGES:+$CHANGES, }plugin $PREV_PLUGIN → $NEW_PLUGIN"
  [ -z "$PREV_PLUGIN" ] && [ -n "$NEW_PLUGIN" ] && CHANGES="${CHANGES:+$CHANGES, }plugin $NEW_PLUGIN (nuevo)"
  if [ -n "$CHANGES" ]; then
    say "   ${G}Frame28 actualizado:${N} $CHANGES."
    say "   Cierra y vuelve a abrir Claude Code para usar la versión nueva."
  else
    say "   ${G}Todo estaba al día${N} (motor $NEW_MOTOR, plugin $NEW_PLUGIN). No he cambiado nada."
  fi
  say "   Para trabajar: abre Claude Code en la carpeta de tu vídeo y pídelo con tus palabras."
  say ""
  say "   Guía completa con imágenes: ${B}$GUIDE${N}"
  say "   Si algo falló, envía el fichero ${B}$LOG${N} a quien te pasó Frame28 o pégaselo a Claude."
  say ""
  exit 0
fi
say "   ${G}Instalación terminada.${N} Cuatro cosas para empezar:"
say "   1. Cierra esta Terminal y abre una nueva (así reconoce los programas nuevos)."
if has claude; then say "   2. Escribe ${B}claude${N} en la Terminal e inicia sesión con tu cuenta de Claude (solo la primera vez)."; else say "   2. Instala Claude Code desde https://claude.com/claude-code e inicia sesión."; fi
say "   3. Entra con tu cuenta de Frame28 (una vez): en la Terminal nueva escribe ${B}claude mcp login plugin:frame28:frame28${N}"
say "      Se abre el navegador: tu email y el código que te llega. Si no tienes cuenta, se crea gratis (modo demo)."
say "      Si dice que no conoce «login», escribe antes ${B}claude update${N} (o dentro de claude: /mcp → frame28 → Authenticate)."
say "   4. Graba un clip hablando a cámara, abre una sesión ${B}nueva${N} de Claude Code (Terminal o app de escritorio) en su carpeta"
say "      y escribe: ${B}\"Aquí está mi clip. Móntamelo.\"${N} (Frame28 sale en las sesiones que empiezan después de entrar.)"
say ""
say "   Guía completa con imágenes: ${B}$GUIDE${N}"
say "   Si algo falló, envía el fichero ${B}$LOG${N} a quien te pasó Frame28 o pégaselo a Claude."
say ""
