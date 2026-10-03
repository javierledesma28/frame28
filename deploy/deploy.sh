#!/usr/bin/env bash
# Despliega frame28.app en t28server (/opt/frame28) desde HEAD (no desde el working tree): sube deploy/ y site/,
# con copia de seguridad del sitio anterior, verifica por hash que el servidor tiene exactamente lo de HEAD y
# levanta nginx (+ túnel si el servidor tiene .env con el token). Se ejecuta desde el PC, en Git Bash:
#
#   deploy/deploy.sh            # despliega HEAD y comprueba https://frame28.app
#   deploy/deploy.sh --check    # solo compara los hashes del servidor con HEAD (no toca nada)
#
# Requisitos: alias SSH `t28server` (~/.ssh/config) con la clave local; árbol commiteado (lo que no está en HEAD
# no se despliega: `git status` te lo recuerda). Fichero en LF: con CRLF bash no lo ejecuta.
set -euo pipefail
# Desde el 2026-10-02 frame28.app se publica desde el repo frame28-app (web/ en Next.js + API + base + copias, con su
# deploy/deploy.sh), en el mismo /opt/frame28. Este script subiría un compose sin API, base ni copias y su remote-up.sh
# (`up -d --remove-orphans`) las BORRARÍA. Se niega siempre que el servidor tenga la plataforma (F28-44); la vuelta atrás
# de frame28.app es `deploy/deploy.sh --rollback` en el repo frame28-app.
HOST=${FRAME28_HOST:-t28server}
DIR=/opt/frame28
# -T: el alias lleva RequestTTY yes y sin terminal ssh avisaría en cada llamada
SSH=(ssh -T -o BatchMode=yes)
if [[ "${1:-}" != "--check" ]]; then
  if ! plat=$("${SSH[@]}" "$HOST" "[ -d $DIR/api ] || [ -f $DIR/backup.sh ] && echo si || echo no"); then
    echo "no se pudo consultar $HOST: por seguridad, no se despliega"; exit 1
  fi
  if [[ "$plat" != "no" ]]; then
    echo "✗ $HOST:$DIR tiene la plataforma (API, base y copias) de frame28-app: este script la borraría. No se despliega."
    echo "  Vuelta atrás de frame28.app: deploy/deploy.sh --rollback en el repo frame28-app."
    exit 1
  fi
  if [[ "${FRAME28_LEGACY_SITE:-}" != "1" ]]; then
    echo "frame28.app se publica desde frame28-app; para subir la landing antigua a un servidor SIN plataforma: FRAME28_LEGACY_SITE=1"
    exit 1
  fi
fi
cd "$(git rev-parse --show-toplevel)"

# Lo que NO forma parte del sitio publicado: fuentes del generador, Markdown de la KB y el curso, y los ficheros de
# Cloudflare Pages (nginx.conf los traduce). deploy/nginx.conf los deniega además por si acaso.
EXCL=(--exclude='site/src' --exclude='site/content' --exclude='site/functions' --exclude='site/build.py'
      --exclude='site/README.md' --exclude='site/wrangler.toml' --exclude='site/_headers' --exclude='site/_redirects')

# sha256sum en Git Bash escribe «hash *ruta» (modo binario) y en Linux «hash  ruta»: se normaliza para comparar.
norm() { sed -E 's/^([0-9a-f]{64}) [ *]/\1  /'; }
manifest_local() {
  local tmp; tmp=$(mktemp -d)
  git archive HEAD site | tar -x -f - -C "$tmp" "${EXCL[@]}"
  (cd "$tmp" && find site -type f | LC_ALL=C sort | xargs sha256sum | norm)
  rm -rf "$tmp"
}
manifest_remote() {
  "${SSH[@]}" "$HOST" "cd $DIR 2>/dev/null && [ -d site ] && find site -type f | LC_ALL=C sort | xargs sha256sum" | norm || true
}
compare() {
  if diff <(manifest_local) <(manifest_remote) >/dev/null; then
    echo "✓ el servidor tiene exactamente el site/ de HEAD ($(git rev-parse --short HEAD))"
  else
    echo "✗ el servidor NO coincide con HEAD:"; diff <(manifest_local) <(manifest_remote) | head -20; return 1
  fi
}

if [[ "${1:-}" == "--check" ]]; then compare; exit $?; fi

if [[ -n "$(git status --porcelain site deploy)" ]]; then
  echo "aviso: hay cambios sin commitear en site/ o deploy/; se despliega HEAD, no el working tree"
fi

echo "1/4 ficheros de despliegue → $HOST:$DIR"
"${SSH[@]}" "$HOST" "mkdir -p $DIR"
git archive HEAD deploy | "${SSH[@]}" "$HOST" "cd $DIR && tar x -f - --strip-components=1 && chmod +x remote-up.sh"

echo "2/4 sitio → $HOST:$DIR/site (copia de seguridad del anterior, se conservan las 3 últimas)"
"${SSH[@]}" "$HOST" "cd $DIR && if [ -d site ]; then mv site .deploy-bak-site-\$(date +%Y%m%d-%H%M%S); fi; ls -d .deploy-bak-site-* 2>/dev/null | head -n -3 | xargs -r rm -rf"
git archive HEAD site | "${SSH[@]}" "$HOST" "cd $DIR && tar x -f - ${EXCL[*]}"

echo "3/4 verificación por hash"
compare

echo "4/4 nginx (+ túnel)"
"${SSH[@]}" "$HOST" "sh $DIR/remote-up.sh"

echo "— comprobación pública —"
for p in / /en/ /fundadores/ /founders /healthz /kb/ /api/contact; do
  printf "  %-14s " "$p"; curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" --max-time 20 "https://frame28.app$p"
done
