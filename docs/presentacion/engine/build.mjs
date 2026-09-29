#!/usr/bin/env node
/* =============================================================================
   FUNDANET DECK · empaquetador
   Convierte un deck de desarrollo (que enlaza el motor por ruta relativa) en un
   único .html autocontenido: sin dependencias, sin red, se abre con doble clic
   y se manda por correo.

     node build/build.mjs decks/demo-tecnica/deck.html
     node build/build.mjs decks/demo-tecnica/deck.html --out dist/mi-deck.html
     node build/build.mjs --all
   ============================================================================= */
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync, statSync } from 'node:fs';
import { dirname, resolve, join, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);

/* Los <link> y <script> locales se sustituyen por su contenido. Los remotos se
   dejan intactos: si alguien añade una fuente de Google, es decisión suya. */
function inline(html, base) {
  html = html.replace(/[ \t]*<link[^>]+rel=["']stylesheet["'][^>]*>/gi, (tag) => {
    const m = tag.match(/href=["']([^"']+)["']/i);
    if (!m || /^https?:|^\/\//i.test(m[1])) return tag;
    const p = resolve(base, m[1]);
    if (!existsSync(p)) { console.warn('  ! no encontrado:', m[1]); return tag; }
    return '<style>\n' + readFileSync(p, 'utf8').trimEnd() + '\n</style>';
  });

  html = html.replace(/[ \t]*<script[^>]+src=["']([^"']+)["'][^>]*><\/script>/gi, (tag, src) => {
    if (/^https?:|^\/\//i.test(src)) return tag;
    const p = resolve(base, src);
    if (!existsSync(p)) { console.warn('  ! no encontrado:', src); return tag; }
    // </script> dentro del código rompería la etiqueta contenedora
    const js = readFileSync(p, 'utf8').replace(/<\/script>/gi, '<\\/script>');
    return '<script>\n' + js.trimEnd() + '\n</script>';
  });

  /* Imágenes locales (logo del cliente, capturas) → data URI. Las remotas y
     las que ya son data: se dejan como están. */
  const MIME = { png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', gif: 'image/gif',
                 webp: 'image/webp', svg: 'image/svg+xml', ico: 'image/x-icon' };
  html = html.replace(/<img\b[^>]*\bsrc=["']([^"']+)["'][^>]*>/gi, (tag, src) => {
    if (/^(https?:|\/\/|data:)/i.test(src)) return tag;
    const p = resolve(base, src);
    if (!existsSync(p)) { console.warn('  ! imagen no encontrada:', src); return tag; }
    const ext = p.split('.').pop().toLowerCase();
    const mime = MIME[ext];
    if (!mime) { console.warn('  ! formato de imagen no soportado:', src); return tag; }
    const b64 = readFileSync(p).toString('base64');
    return tag.replace(src, `data:${mime};base64,${b64}`);
  });

  return html;
}

function build(srcRel, outRel) {
  const src = resolve(ROOT, srcRel);
  if (!existsSync(src)) { console.error('No existe:', srcRel); process.exit(1); }

  const raw = readFileSync(src, 'utf8');
  const out = inline(raw, dirname(src));

  const slides = (out.match(/class="slide\b/g) || []).length;
  const notes  = (out.match(/class="s-notes"/g) || []).length;

  const dest = resolve(ROOT, outRel || join('dist', basename(dirname(src)) + '.html'));
  mkdirSync(dirname(dest), { recursive: true });
  writeFileSync(dest, out, 'utf8');

  const kb = (Buffer.byteLength(out, 'utf8') / 1024).toFixed(0);
  const externo = /<(link[^>]+href|script[^>]+src)=["']https?:/i.test(out);

  console.log(`  ${basename(dest).padEnd(30)} ${String(kb).padStart(5)} KB  ` +
              `${slides} slides  ${notes} con notas  ` +
              `${externo ? 'CON dependencias remotas' : 'autocontenido'}`);
  return dest;
}

if (args.includes('--all')) {
  const dir = resolve(ROOT, 'decks');
  console.log('Empaquetando todos los decks:');
  for (const d of readdirSync(dir)) {
    const f = join(dir, d, 'deck.html');
    if (existsSync(f) && statSync(f).isFile()) build(join('decks', d, 'deck.html'));
  }
} else if (args[0]) {
  const oi = args.indexOf('--out');
  console.log('Empaquetando:');
  build(args[0], oi > -1 ? args[oi + 1] : null);
} else {
  console.log('Uso:\n  node build/build.mjs <deck.html> [--out dist/x.html]\n  node build/build.mjs --all');
  process.exit(1);
}
