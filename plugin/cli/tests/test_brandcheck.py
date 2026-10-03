"""Nota de marca del storyboard (F28-24): lectura de las reglas (marca, brief del MCP, Memoria), cada comprobación, la
nota y la orden `frame28 storyboard brandcheck`."""
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from frame28 import brandcheck as B
from frame28.cli import main

ROOT = Path(__file__).resolve().parents[3]

# El brief tal como lo escriben frame28_memoria + frame28_campana (repo frame28-app, memoria.brief y campana.brief)
BRIEF = """# Memoria de marca · Acme Kits · v3
Hazlo tú · https://acme.example
Colores: acento `#E4572E`, tinta `#111111`, papel `#FFFFFF` · tipografía Inter

## Sin confirmar
Claude dedujo estos campos de https://acme.example y el cliente todavía no los ha revisado: `story.proof`.

## Voz
- Pilares: cercano, práctico
- Trato: tú
- Frases de 8 palabras como mucho
- Emojis: no · mayúsculas en ganchos: sí
- Nunca digas: revolucionario, mágico

## Ganchos prohibidos
- Increíble truco

## Glosario (términos fijos por idioma)
- en: grabador → engraver; Kit de inicio → Starter Kit

## Reglas legales (prevalecen sobre todo lo demás)
- No afirmar: garantizado, cura
- Resultados según el uso.

# Campaña · Lanzamiento · Acme Kits · toma 2
Estado: Lista para montar · Objetivo: **Vender**

## Tiene que decirse (literal o casi)
- Envío gratis esta semana

## Esta campaña no dice
- profesional
"""
BRAND = {"name": "Acme", "accent": "#E4572E", "ink": "#111111", "paper": "#FFFFFF"}


def sb(overlays, captions=None, **extra):
    return {"version": 1, "source": {"video": "clip.mp4", "duration": 30}, "canvas": {"width": 1920, "height": 1080},
            "overlays": overlays, "captions": captions or [], **extra}


def test_reglas_del_brief():
    r = B.rules_from_brief(BRIEF)
    assert r.avoid == ["revolucionario", "mágico", "profesional"]
    assert r.claims == ["garantizado", "cura"] and r.banned_hooks == ["Increíble truco"]
    assert r.glossary == {"en": {"grabador": "engraver", "Kit de inicio": "Starter Kit"}}
    assert r.must_say == ["Envío gratis esta semana"] and r.max_words == 8
    assert B.rules_from_brief("# nada\n").empty()


def test_reglas_de_la_marca_y_de_la_memoria_se_suman():
    think28 = json.loads((ROOT / "plugin/cli/frame28/brands/think28.json").read_text(encoding="utf-8"))
    r = B.rules_from_brand(think28, "think28")
    assert "disruptivo" in r.avoid and r.max_words == 15 and r.sources == ["think28"]
    m = B.rules_from_memoria({"voice": {"avoid": ["disruptivo", "único"]}, "legal": {"claims_not_allowed": ["el mejor"]},
                              "hooks": {"banned": ["No vas a creer"]}, "glossary": {"de": {"kit": "Set"}}}, "m.json")
    r.add(m)
    assert r.avoid.count("disruptivo") == 1 and "único" in r.avoid and r.claims == ["el mejor"]
    assert r.glossary == {"de": {"kit": "Set"}} and r.sources == ["think28", "m.json"] and r.max_words == 15
    assert B.rules_from_brand({}).empty() and B.rules_from_brand({}).sources == []


def test_coincidencias_sin_acentos_ni_falsos_positivos():
    assert B.found("garantizado", "Resultados GARANTIZADOS")              # plural y mayúsculas
    assert B.found("garantizado", "satisfacción garantizada")            # femenino
    assert B.found("mágico", "Un truco MAGICO")                          # sin tilde
    assert not B.found("cura", "seguridad asegurada")                    # palabra corta: exacta
    assert not B.found("cura", "procuramos")
    assert B.found("el mejor", "Es el mejor kit") and not B.found("el mejor", "el mejorado")


def test_cada_regla_y_la_nota():
    rules = B.rules_from_brief(BRIEF)
    story = sb([
        {"type": "box", "id": "b1", "start": 1, "end": 3, "x": 100, "y": 100, "text": "Resultados garantizados"},
        {"type": "kinetic", "id": "k1", "start": 3, "end": 5, "x": 100, "y": 400,
         "lines": [[{"text": "Un", "at": 3}, {"text": "kit", "at": 3.2}, {"text": "mágico", "at": 3.4}]]},
        {"type": "hook", "id": "h1", "start": 0, "end": 2, "text": "Increíble truco"},
        {"type": "card", "id": "c1", "start": 6, "end": 8, "bg": "accent", "color": "accent", "title": {"text": "Hola"}},
        {"type": "card", "id": "c2", "start": 8, "end": 9, "bg": "white", "color": "#DDDDDD", "title": {"text": "Gris"}},
        {"type": "pointer", "id": "p1", "start": 9, "end": 11, "dot": [1, 1], "box": [2, 2],
         "text": "Este grabador corta madera en muy pocos minutos sin esfuerzo"},
    ], captions=[{"start": 0, "end": 2, "text": "Te lo dejo garantizado"}], meta={"lang": "en"})
    r = B.check(story, rules, BRAND)
    by = {}
    for i in r["issues"]:
        by.setdefault(i["rule"], []).append(i["id"])
    assert by["legal"] == ["b1"] and by["avoid"] == ["k1"] and by["banned_hook"] == ["h1"]
    assert by["accent_on_accent"] == ["c1"] and by["contrast"] == ["c2"]
    assert by["glossary"] == ["p1"] and by["long_sentence"] == ["p1"] and by["density"] == ["p1"]
    assert by["voice_claim"] == ["captions"] and by["must_say"] == ["campaña"]
    assert r["errors"] == 4 and r["lang"] == "en"
    assert r["score"] == max(0, 100 - sum(B.PENALTY[i["rule"]] for i in r["issues"])) and r["score"] < 20
    assert all(i["fix"] for i in r["issues"])                            # cada fallo dice cómo arreglarlo


def test_un_storyboard_limpio_saca_100():
    rules = B.rules_from_brief(BRIEF)
    story = sb([{"type": "cta", "id": "cta", "start": 20, "end": 25, "title": "Envío gratis esta semana", "bg": "black"},
                {"type": "box", "id": "b", "start": 1, "end": 3, "x": 100, "y": 100, "text": "Tu primer grabado"}])
    r = B.check(story, rules, BRAND, lang="es")
    assert r["score"] == 100 and r["issues"] == [] and r["errors"] == 0


def test_zonas_seguras_en_vertical():
    story = sb([{"type": "box", "id": "abajo", "start": 1, "end": 3, "x": 100, "y": 1800, "text": "Hola"}],
               canvas={"width": 1080, "height": 1920}, platform="tiktok")
    r = B.check(story, B.Rules(max_words=20), BRAND)
    assert [i["rule"] for i in r["issues"]] == ["safe_zone"] and r["issues"][0]["id"] == "abajo"


def test_textos_en_pantalla_de_todos_los_tipos():
    story = sb([
        {"type": "lower_third", "id": "l", "start": 0, "end": 1, "x": 0, "y": 0, "title": "Ana", "subtitle": "Fundadora"},
        {"type": "list_focus", "id": "lf", "start": 0, "end": 1, "items": [{"text": "Uno", "at": 0}]},
        {"type": "chart", "id": "ch", "start": 0, "end": 1, "kind": "bar", "series": [{"label": "Antes", "value": 1}], "title": "Tiempo"},
        {"type": "steps", "id": "st", "start": 0, "end": 1, "items": [{"label": "Calca", "at": 0}]},
        {"type": "hook", "id": "hk", "start": 0, "end": 1, "lines": ["Línea uno", "línea dos"]},
        {"type": "brand_card", "id": "bc", "start": 0, "end": 1, "endorsement": "Un producto de Acme"},
    ])
    got = {(o["id"], where): t for o, where, t in B.screen_texts(story)}
    assert got[("l", "subtitle")] == "Fundadora" and got[("lf", "items[0]")] == "Uno" and got[("ch", "series[0]")] == "Antes"
    assert got[("st", "items[0]")] == "Calca" and got[("hk", "lines")] == "Línea uno línea dos" and got[("bc", "endorsement")]


def test_contraste_wcag():
    assert B.contrast("#000000", "#FFFFFF") == 21.0 and B.contrast("#FFFFFF", "#FFFFFF") == 1.0
    assert B.contrast("accent", "#FFFFFF") is None


def test_orden_brandcheck_y_validate(tmp_path):
    work = tmp_path / "work"
    (work / "cut").mkdir(parents=True)
    (work / "brief.md").write_text(BRIEF, encoding="utf-8")                # el brief vive en work/, el storyboard en work/cut/
    bad = work / "cut" / "storyboard.json"
    bad.write_text(json.dumps(sb([{"type": "box", "id": "b1", "start": 1, "end": 3, "x": 1, "y": 1, "text": "Cura garantizada"}],
                                 brand=BRAND)), encoding="utf-8")
    run = CliRunner()
    r = run.invoke(main, ["storyboard", "brandcheck", str(bad)])
    assert r.exit_code == 1 and "Nota de marca:" in r.output and "legal" in r.output and "→" in r.output and "brief.md" in r.output
    r = run.invoke(main, ["storyboard", "brandcheck", str(bad), "--json"])
    data = json.loads(r.output)
    assert data["errors"] >= 1 and data["rules"]["claims"] == 2
    r = run.invoke(main, ["storyboard", "validate", str(bad)])
    assert r.exit_code == 0 and "Storyboard válido." in r.output and "Nota de marca:" in r.output   # validate no bloquea por la nota
    good = work / "cut" / "ok.json"
    good.write_text(json.dumps(sb([{"type": "cta", "id": "c", "start": 1, "end": 3, "title": "Envío gratis esta semana"}], brand=BRAND)),
                    encoding="utf-8")
    r = run.invoke(main, ["storyboard", "brandcheck", str(good), "--min", "90"])
    assert r.exit_code == 0 and "Sin fallos." in r.output
    alone = tmp_path / "solo.json"
    alone.write_text(json.dumps(sb([], brand=BRAND)), encoding="utf-8")
    r = run.invoke(main, ["storyboard", "brandcheck", str(alone)])
    assert r.exit_code == 0 and "Nada que comprobar" in r.output


@pytest.mark.parametrize("path", sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("poc/*/storyboard*.json")))
def test_storyboards_reales_no_rompen(path):
    """Los storyboards versionados (marca think28 y de cliente) pasan por la nota sin romper y con fallos bien formados."""
    sb_path = ROOT / path
    story, rules, brand = B.load(sb_path)
    r = B.check(story, rules, brand)
    assert 0 <= r["score"] <= 100
    for i in r["issues"]:
        assert set(i) >= {"rule", "severity", "id", "type", "message", "fix"} and i["rule"] in B.PENALTY
