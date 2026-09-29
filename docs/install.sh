#!/bin/sh
# Frame28 · instalador para macOS (y Linux con apt)
# Uso (una sola línea, en Terminal):
#   curl -fsSL https://frame28.t28.io/install.sh | sh
#
# Qué hace, en orden, y solo lo que falte:
#   1. ffmpeg, Node.js y uv con Homebrew (macOS) o apt + curl (Linux)
#   2. El motor de Frame28 (CLI `frame28`) con uv, desde GitHub
#   3. El plugin de Claude Code, si `claude` está instalado
#   4. `frame28 doctor` para comprobar que todo está en su sitio
# Es seguro ejecutarlo varias veces: si algo ya está, lo salta.
set -e
REPO="https://github.com/javierledesma28/frame28"
MARKET="javierledesma28/frame28"
Y='\033[33m'; G='\033[32m'; R='\033[31m'; D='\033[90m'; N='\033[0m'
step() { printf "\n${Y}==> %s${N}\n" "$1"; }
ok()   { printf "    ${G}OK  %s${N}\n" "$1"; }
skip() { printf "    ${D}--  %s${N}\n" "$1"; }
has()  { command -v "$1" >/dev/null 2>&1; }

printf "\n${Y}  Frame28 · A Think28 product · instalador para macOS${N}\n  Graba hablando a cámara. Frame28 monta el resto.\n"

OS=$(uname -s)
if [ "$OS" = "Darwin" ]; then
  if ! has brew; then
    printf "${R}No encuentro Homebrew. Instálalo con la línea de https://brew.sh y vuelve a ejecutar esto.${N}\n"; exit 1
  fi
  for pair in "ffmpeg:ffmpeg" "node:node" "uv:uv"; do
    cmd=${pair%%:*}; pkg=${pair##*:}
    step "$pkg"
    if has "$cmd"; then skip "ya instalado"; else brew install "$pkg" >/dev/null && ok "instalado"; fi
  done
else
  step "ffmpeg, Node.js y uv (Linux)"
  has ffmpeg || (sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg >/dev/null && ok "ffmpeg")
  has node || (curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - >/dev/null && sudo apt-get install -y -qq nodejs >/dev/null && ok "node")
  has uv || (curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null && ok "uv")
fi

# uv deja sus herramientas en ~/.local/bin
export PATH="$HOME/.local/bin:$PATH"

step "Motor de Frame28 (frame28)"
uv tool install --python 3.12 --force "git+$REPO#subdirectory=plugin/cli" >/dev/null
uv tool update-shell >/dev/null 2>&1 || true
if has frame28; then ok "frame28 $(frame28 --version | awk '{print $NF}')"; else printf "${R}    frame28 no está en el PATH: abre una terminal nueva y escribe 'frame28 doctor'.${N}\n"; fi

step "Plugin de Claude Code"
if has claude; then
  claude plugin marketplace add "$MARKET" >/dev/null 2>&1 || true
  if claude plugin install "frame28@think28" --scope user >/dev/null 2>&1; then ok "frame28@think28 instalado (reinicia Claude Code para que lo cargue)"; else printf "${R}    No pude instalar el plugin. En Claude Code escribe: /plugin marketplace add %s  y luego  /plugin install frame28@think28${N}\n" "$MARKET"; fi
else
  skip "Claude Code no está instalado o no está en el PATH. Descárgalo de https://claude.com/claude-code y luego, dentro de Claude Code, escribe:"
  printf "        /plugin marketplace add %s\n        /plugin install frame28@think28\n" "$MARKET"
fi

step "Comprobación final"
has frame28 && frame28 doctor || true
printf "\n${Y}  Listo. Guía de uso: https://frame28.t28.io/presentacion/${N}\n\n"
