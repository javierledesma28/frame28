# Clip "auriculares" · anuncio de 58 s montado con el pipeline completo (2026-09-30)

Segundo clip real del usuario (webcam 1080p60, 58 s, español). Es el primer montaje "de producto" completo:

1. `frame28 prep` → voz limpia (−33 → −14 LUFS), 30 fps.
2. `frame28 transcribe` → 91 palabras, 6 frases.
3. `frame28 cut plan/apply` → 6 tramos de silencio fuera (58,0 → 51,9 s), sin falsos positivos.
4. `frame28 speaker` (centrado) + `frame28 gestures` → 5 gestos; el de "por esta zona" (16,7 s) con confianza alta,
   y el gesto de enseñar el producto (8,7 s) aprovechado como pointer "estos auriculares".
5. `frame28 matte` solo en 31,9–34,8 s para "SUDAMÉRICA" detrás del hablante.
6. `storyboard.json` (17 overlays): rótulo, cinéticos con máscara, dos contadores (10× en acento, 3× en negro),
   check dibujado, flechas "de este a oeste", tarjeta de marca. Render 4 min 23 s.

Lección: en un contador sobre fondo de acento el sufijo "×" iba en el mismo amarillo y no se veía; corregido en
`build.py` (`.counter.accent .num b`). Los medios y `work/` no se versionan; el storyboard y `cuts.json` sí.
