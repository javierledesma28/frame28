#!/usr/bin/env sh
# Se ejecuta EN EL SERVIDOR (lo sube y lo llama deploy.sh desde /opt/frame28): comprueba la configuración de nginx
# en un contenedor aparte (un error de sintaxis dejaría el sitio caído), levanta el web y, si .env trae el token,
# el túnel de Cloudflare.
set -eu
cd "$(dirname "$0")"

echo "   comprobando nginx.conf…"
# Sin tubería: el estado de salida de `nginx -t` tiene que parar el script si falla.
docker run --rm -v "$PWD/nginx.conf:/etc/nginx/conf.d/default.conf:ro" nginx:alpine nginx -t

PROFILES=""
if [ -s .env ] && grep -q '^CLOUDFLARE_TUNNEL_TOKEN=.\+' .env; then
  PROFILES="--profile tunnel"
else
  echo "   (sin .env con CLOUDFLARE_TUNNEL_TOKEN: solo web, sin túnel; crea .env a partir de .env.example)"
fi

# --force-recreate en web: nginx.conf va como bind mount de un fichero y tar/scp cambian el inodo, así que un
# contenedor ya creado seguiría leyendo la configuración antigua.
# shellcheck disable=SC2086
docker compose $PROFILES up -d --remove-orphans --force-recreate web
case "$PROFILES" in *tunnel*) docker compose $PROFILES up -d tunnel ;; esac
# shellcheck disable=SC2086
docker compose $PROFILES ps
