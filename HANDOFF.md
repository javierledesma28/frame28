# Traspaso · motor y plugin de Frame28 (2026-10-19)

Estado verificado del repo para la sesión siguiente. Lo permanente (qué hay, cómo se ejecuta, cómo se publica una
release, decisiones y trampas) está en [CLAUDE.md](CLAUDE.md); las normas del equipo, en
`C:/Workspaces/personal/frame28-backlog/NORMAS.md`; **el trabajo pendiente, en el backlog común** (tareas F28-N:
`python -X utf8 C:/Workspaces/personal/frame28-backlog/backlog.py lista`, o el tablero). Aquí no se listan tareas: lo
que haya que hacer está en el backlog, y lo de frame28.app (landing, panel, MCP, método, precios) en el repo `frame28-app`.

## Estado

| Qué | Estado el 2026-10-19 |
|---|---|
| Release | **v0.6.0** publicada y marcada como última en GitHub; tag `v0.6.0` → `3bbb292`. La rama `release` está en ese commit: de ella instalan el instalador, el plugin y `uv tool upgrade` (F28-91) |
| `main` | Por delante de `release` solo con documentación (cabecera del roadmap, este traspaso y `CLAUDE.md`) |
| Plugin | Diez skills cáscara y `.mcp.json` → `https://frame28.app/mcp` (OAuth con Frame28 ID). El método, la Memoria de marca y las campañas los sirve frame28.app |
| CLI | `frame28 --version` → 0.6.0; 26 órdenes en 23 módulos; extras `probado` (versiones exactas) y `gpu` |
| Pruebas | 368 en un worktree y 372 en la carpeta principal (allí también recorre los casos locales del Cliente A), sin ffmpeg ni modelos; CI en cada push que toque `plugin/cli/` |
| Instalación limpia | Verificada tras publicar la v0.6.0: el motor desde `@release` con `[probado]` y el plugin desde el marketplace, en entornos aislados |
| Web del plugin | frame28.t28.io (GitHub Pages sobre `docs/`): guía, asistente de instalación, instaladores y roadmap |
| Roadmap | v0.6.0 publicada («se instala lo que se probó»); siguiente, v0.7.0 «calidad y alcance». Artefacto de claude.ai republicado (versión 14) |

## Confidencialidad del Cliente A en este repo

- Lo que lo nombra vive en `_private/` (solo en la carpeta principal, ignorado): material del cliente, la lista de sus
  casos locales (`_private/cliente-a/casos-locales.md`), `confidencial.txt` con los términos que busca `release-check` y
  las copias de la historia anterior a cada reescritura.
- Sus casos están en `poc/` solo en local, fuera de git por `.git/info/exclude`. El caso público, `poc/clip-tutorial`, es
  inventado (F28-99).
- La historia se reescribió el 2026-10-01 y el 2026-10-19 (A-222). El gancho `.git/hooks/pre-push` de este clon impide
  volver a publicar la vieja: las ramas locales anteriores al 2026-10-19 la contienen y hay que rebasarlas antes de
  subirlas.
- **Abierto:** los commits viejos siguen accesibles por su SHA en la API de GitHub hasta que soporte purgue la caché
  (A-306, lo pide Javier). Cuando conteste, comprobar que el SHA de la historia vieja que usa el gancho pre-push da 404
  con `gh api repos/javierledesma28/frame28/commits/<sha>`.

## Lo que espera a Javier

- Revisión de F28-99 (caso público inventado) y F28-109 (motor de la presentación sin marca), y de este traspaso (F28-132).
- A-306: la purga de GitHub.
- Las tareas del área marcadas «necesita a Javier» en el backlog: probar desde Cowork y la app de escritorio (F28-25),
  la Memoria de punta a punta (F28-10), claves de Pexels y Pixabay para el B-roll (F28-17) y el doblaje (F28-26).

## Para retomar

```bash
git -C C:/Workspaces/personal/Skill-Director fetch origin && git -C C:/Workspaces/personal/Skill-Director status -sb
ssh -T git@github-jl28                                  # «Hi javierledesma28!»
git -C C:/Workspaces/personal/Skill-Director worktree list   # trabajar en un worktree propio, nunca en la carpeta principal
frame28 doctor                                          # «Todo listo.»; origen del motor, versiones probadas, cuenta de Frame28
claude plugin validate C:/Workspaces/personal/Skill-Director/plugin
cd <worktree>/plugin/cli && uv run --extra probado --group dev pytest
python -X utf8 scripts/release-check.py --notes         # desde la carpeta principal (allí está _private/)
cd poc/clip-javier && frame28 build storyboard-gsap.json -o work/f28-gsap && frame28 check work/f28-gsap && frame28 render work/f28-gsap -o out/test.mp4 --workers 10
```

Si ffmpeg o uv no están en el PATH de la shell, el CLI los encuentra solo; para la shell, la línea `export PATH` de las
Trampas de `CLAUDE.md`. Antes de fiarte de este fichero, `git log` y los `.frame28/log.jsonl` de `poc/*/` dicen lo que
de verdad se hizo.
