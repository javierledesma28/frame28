# frame28.app · sitio del producto

Estático, servido por **Cloudflare Pages** desde esta carpeta, sin build en el despliegue: el HTML se genera aquí
con `build.py` y se commitea. El plugin abierto sigue en frame28.t28.io (GitHub Pages sobre `docs/`).

```
content/      textos fuente: landing.{es,en}.md (referencia editorial), condiciones.es.md y terms.en.md (se convierten a HTML)
src/{es,en}/  fragmentos HTML de cada página (lo que va dentro de <main>)
build.py      plantilla común + fragmentos + condiciones → index.html, en/, fundadores/, contacto/, condiciones/, en/founders/, en/contact/, en/terms/
assets/       site.css, favicon.svg (isotipo Think28), think28-horizontal.svg
functions/api/contact.js   formulario de contacto (Pages Function → email)
_redirects, _headers, wrangler.toml
```

## Editar y regenerar

1. Textos: `src/{es,en}/*.html` (landing, Fundadores, contacto) o `content/condiciones.es.md` / `terms.en.md`.
   `content/landing.*.md` son la referencia editorial de la landing; si cambias un texto ahí, cámbialo también en `src/`.
2. Plazas de Fundadores, buzón y si el caso de cliente es público (y con qué nombre): `CONFIG` en `build.py`.
3. Regenerar desde la raíz del repo: `uv run --with markdown python site/build.py`.
4. Previsualizar sin Cloudflare: `python -m http.server 8080 -d site` y abrir http://localhost:8080/ (el formulario
   fallará con error visible porque no hay `/api/contact`; eso es lo esperado). Con wrangler:
   `npx wrangler pages dev site` sirve también la función (sin binding de email, escribe el mensaje en el log).

## Desplegar en Cloudflare Pages (una vez)

1. Workers & Pages → Create → Pages → **Connect to Git** → repo `javierledesma28/frame28`, rama `main`.
2. Build settings: framework **None**, build command vacío, **root directory `site`**, build output directory `/`
   (o `.`); Pages detecta `functions/` y `wrangler.toml` dentro de `site/`.
3. Custom domains → `frame28.app` (y `www.frame28.app` → redirección). El dominio ya está en Cloudflare, así que
   el CNAME lo crea solo.
4. Email: en el panel de Cloudflare, Email → verificar el dominio frame28.app como remitente y crear el buzón o
   la ruta de `hola@frame28.app` (Email Routing hacia el buzón real de Javier). Si el binding `send_email` no
   aparece al desplegar, añadirlo en Settings → Bindings con el nombre `SEND_EMAIL`. [[verificar: el API de envío
   de Email Service está en beta; `functions/api/contact.js::sendMail` es el único sitio que tocar]]
5. Probar el formulario en producción (ES y EN) y comprobar que el email llega con `Reply-To` del remitente.
6. Base de conocimiento y curso (`/kb/*`, `/curso/*`, pendientes): Zero Trust → Access → aplicación sobre
   `frame28.app/kb*` y `/curso*` con política "código de un solo uso por email" y la lista de clientes.

## Pendiente antes de publicar

- `assets/og.png` generada desde `assets/og.html` (1200×630, captura con Chromium); regenerar si cambia la promesa.
- Rellenar los huecos `[[…]]` de las condiciones (datos fiscales, fuero, buzón) tras la revisión legal; `build.py`
  los resalta en amarillo mientras existan y cuenta cuántos quedan.
- `CONFIG["case_public"] = True` con `case_brand` y crear `casos/<marca>/` cuando el cliente autorice por escrito; hasta entonces `_redirects`
  manda esa ruta al contacto.
