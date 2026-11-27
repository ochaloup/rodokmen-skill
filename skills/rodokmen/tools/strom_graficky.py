#!/usr/bin/env python3
"""Grafický „středověký“ strom (přímá linie nebo vývod, "typ": "vyvod"): data/strom_*.json -> SVG + PNG + PDF (Inkscape).

Použití: python3 -I tools/strom_graficky.py data/strom_linie_rodu.json [výstupní_složka]
"""
import json
import os
import subprocess
import sys
from xml.sax.saxutils import escape

W, H = 4220, 5964
STRED = 2110
KARTA_W, KARTA_H = 1300, 450
HNEDA, TMAVA, PAPIR = "#6b4a22", "#3b2a14", "#f8eed6"
NADPIS_PISMO = "Linux Libertine Display O"
PISMO = "Linux Libertine O"
ERBY = {}


def erb(obec, x, y, vyska):
    z = ERBY.get(obec)
    if not z:
        return ""
    return (f'<image x="{x}" y="{y}" width="{vyska * 0.85}" height="{vyska}" preserveAspectRatio="xMidYMid meet" '
            f'xlink:href="file://{escape(z)}"/>')


RIMSKE = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI"]
LINIE = "#8b2a1a"


def karta(x, y, radky, w=KARTA_W, h=KARTA_H, m=1.0, znak=None, vpravo=False, linie=False):
    o = 18 * m
    out = [
        f'<g transform="translate({x},{y})">',
        f'<rect x="0" y="0" width="{w}" height="{h}" rx="{46 * m}" fill="{PAPIR}" fill-opacity="0.84" '
        f'stroke="{LINIE if linie else HNEDA}" stroke-width="{(14 if linie else 7) * m}" filter="url(#stin)"/>',
        f'<rect x="{o}" y="{o}" width="{w - 2 * o}" height="{h - 2 * o}" rx="{32 * m}" fill="none" stroke="{HNEDA}" stroke-width="{2.5 * m}"/>',
    ]
    for cx, cy in ((o, o), (w - o, o), (o, h - o), (w - o, h - o)):
        k = 16 * m
        out.append(f'<path d="M{cx},{cy - k} L{cx + k},{cy} L{cx},{cy + k} L{cx - k},{cy} Z" fill="{HNEDA}"/>')
    jmeno, *dalsi = radky
    stredx = w / 2
    if znak and znak in ERBY:
        vys = min(h - 70 * m, 230 * m)
        zx = w - 45 * m - vys * 0.85 if vpravo else 45 * m
        out.append(erb(znak, zx, (h - vys) / 2, vys))
        stredx = w / 2 + (-90 * m if vpravo else 90 * m)
    out.append(f'<text x="{stredx}" y="{150 * m}" font-family="{NADPIS_PISMO}" font-size="{86 * m}" fill="{TMAVA}" '
               f'text-anchor="middle">{escape(jmeno)}</text>')
    out.append(f'<path d="M{stredx - 260 * m},{190 * m} Q{stredx},{215 * m} {stredx + 260 * m},{190 * m}" stroke="{HNEDA}" stroke-width="{3 * m}" fill="none"/>')
    for i, r in enumerate(dalsi):
        if not r:
            continue
        styl = 'font-style="italic" ' if i >= 1 else ""
        vel = (62 if i == 0 else 52) * m
        out.append(f'<text x="{stredx}" y="{(285 + i * 78) * m}" font-family="{PISMO}" {styl}font-size="{vel}" '
                   f'fill="{TMAVA}" text-anchor="middle">{escape(r)}</text>')
    out.append("</g>")
    return "\n".join(out)


def medailon(cy, gen, snatek, m=1.0):
    out = [f'<circle cx="{STRED}" cy="{cy}" r="{92 * m}" fill="{PAPIR}" stroke="{HNEDA}" stroke-width="{7 * m}" filter="url(#stin)"/>',
           f'<circle cx="{STRED}" cy="{cy}" r="{76 * m}" fill="none" stroke="{HNEDA}" stroke-width="2.5"/>',
           f'<text x="{STRED}" y="{cy + 30 * m}" font-family="{NADPIS_PISMO}" font-size="{(80 if len(gen) < 4 else 62) * m}" '
           f'fill="{TMAVA}" text-anchor="middle">{gen}</text>']
    if snatek:
        out.append(f'<rect x="{STRED - 130 * m}" y="{cy + 108 * m}" width="{260 * m}" height="{78 * m}" rx="20" fill="{PAPIR}" '
                   f'fill-opacity="0.92" stroke="{HNEDA}" stroke-width="4"/>')
        out.append(f'<text x="{STRED}" y="{cy + 164 * m}" font-family="{PISMO}" font-size="{52 * m}" fill="{TMAVA}" '
                   f'text-anchor="middle">× {escape(snatek)}</text>')
    return "\n".join(out)


def svg(data, koren):
    pozadi = os.path.abspath(os.path.join(koren, data["pozadi"]))
    gen = data["generace"]
    horni, dolni = 600, 4720
    krok = (dolni - horni) / max(1, len(gen) - 1)
    casti = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<defs><filter id="stin" x="-10%" y="-10%" width="120%" height="130%">'
        '<feGaussianBlur in="SourceAlpha" stdDeviation="10"/><feOffset dx="6" dy="10" result="o"/><feComponentTransfer><feFuncA type="linear" slope="0.35"/></feComponentTransfer><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
        f'<image x="0" y="0" width="{W}" height="{H}" xlink:href="file://{escape(pozadi)}"/>',
        f'<rect x="760" y="40" width="2700" height="250" rx="60" fill="{PAPIR}" fill-opacity="0.9" stroke="{HNEDA}" '
        f'stroke-width="8" filter="url(#stin)"/>',
        f'<text x="{STRED}" y="185" font-family="{NADPIS_PISMO}" font-size="150" fill="{TMAVA}" text-anchor="middle">'
        f'{escape(data["nadpis"])}</text>',
        f'<text x="{STRED}" y="262" font-family="{PISMO}" font-style="italic" font-size="58" fill="{TMAVA}" '
        f'text-anchor="middle">{escape(data.get("podnadpis", ""))}</text>',
    ]
    m = min(1.0, krok / (KARTA_H + 40))
    kw, kh = KARTA_W * m, KARTA_H * m
    for i, g in enumerate(gen):
        cy = dolni - i * krok
        y = cy - kh / 2
        mz, zn = g["muz"], g["zena"]
        casti.append(karta(STRED - 550 - kw, y, mz["radky"], w=kw, h=kh, m=m, znak=mz.get("erb"), linie=mz.get("linie", False)))
        casti.append(karta(STRED + 550, y, zn["radky"], w=kw, h=kh, m=m, znak=zn.get("erb"), vpravo=True,
                           linie=zn.get("linie", False)))
        casti.append(medailon(cy - 40 * m, RIMSKE[i + 1], g.get("snatek"), m))
    d = data["dite"]
    dw = d.get("sirka", KARTA_W)
    casti.append(karta(STRED - dw / 2, 5320, d["radky"], w=dw, h=380, znak=d.get("erb"), linie=True))
    casti.append(medailon(5185, "I", None))
    casti.append("</svg>")
    return "\n".join(casti)


def vyvod(data, koren):
    vw, vh = 5964, 4220
    pozadi = os.path.abspath(os.path.join(koren, data["pozadi"]))
    os_ = data["osoby"]
    sest = "63" in os_
    if sest:   # 6. generace ve dvou řadách nad sebou (střídavě), jinak se 32 kartiček na šířku nevejde
        rady = {6: (32, 340, 300, 0.3), 5: (16, 320, 760, 0.4), 4: (8, 640, 1330, 0.62), 3: (4, 860, 2060, 0.78),
                2: (2, 980, 2830, 0.86), 1: (1, 1080, 3600, 0.9)}
    else:
        rady = {5: (16, 350, 320, 0.4), 4: (8, 640, 1150, 0.62), 3: (4, 860, 1980, 0.78), 2: (2, 980, 2800, 0.86), 1: (1, 1080, 3600, 0.9)}
    poloha = {}
    for g, (n, w, y, m) in rady.items():
        prvni = 2 ** (g - 1)
        krok = (vw - 300) / n
        for i in range(n):
            cx = 150 + krok * (i + 0.5)
            yy = y + (190 if g == 6 and i % 2 else 0)
            poloha[prvni + i] = (cx, yy, w, m * (250 + 78 * max(1, len(os_[str(prvni + i)]) - 1)), m)
    casti = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{vw}" height="{vh}" viewBox="0 0 {vw} {vh}">',
        '<defs><filter id="stin" x="-10%" y="-10%" width="120%" height="130%">'
        '<feGaussianBlur in="SourceAlpha" stdDeviation="8"/><feOffset dx="5" dy="8" result="o"/><feComponentTransfer><feFuncA type="linear" slope="0.35"/></feComponentTransfer><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
        f'<image x="0" y="0" width="{vw}" height="{vh}" xlink:href="file://{escape(pozadi)}"/>',
        f'<rect x="{vw / 2 - 1500}" y="40" width="3000" height="230" rx="60" fill="{PAPIR}" fill-opacity="0.9" stroke="{HNEDA}" stroke-width="8" filter="url(#stin)"/>',
        f'<text x="{vw / 2}" y="175" font-family="{NADPIS_PISMO}" font-size="140" fill="{TMAVA}" text-anchor="middle">{escape(data["nadpis"])}</text>',
        f'<text x="{vw / 2}" y="245" font-family="{PISMO}" font-style="italic" font-size="54" fill="{TMAVA}" text-anchor="middle">{escape(data.get("podnadpis", ""))}</text>',
    ]
    for k in range(1, 32 if sest else 16):
        cx, y, w, h, m = poloha[k]
        for r in (2 * k, 2 * k + 1):
            px, py, pw, ph, pm = poloha[r]
            casti.append(f'<path d="M{cx},{y} C{cx},{(y + py + ph) / 2} {px},{(y + py + ph) / 2} {px},{py + ph}" '
                         f'stroke="{HNEDA}" stroke-width="6" stroke-opacity="0.75" fill="none"/>')
    for k, (cx, y, w, h, m) in poloha.items():
        casti.append(karta(cx - w / 2, y, os_[str(k)], w=w, h=h, m=m))
    panel = [e for e in data.get("erby_panel", []) if e["obec"] in ERBY]
    pul = (len(panel) + 1) // 2
    for strana, skupina in ((0, panel[:pul]), (1, panel[pul:])):
        x0 = 90 if strana == 0 else vw - 90 - 2 * 470
        for j, e in enumerate(skupina):
            x = x0 + (j % 2) * 470
            y = 3060 + (j // 2) * 380
            casti.append(f'<rect x="{x}" y="{y}" width="440" height="350" rx="30" fill="{PAPIR}" fill-opacity="0.8" '
                         f'stroke="{HNEDA}" stroke-width="4" filter="url(#stin)"/>')
            casti.append(erb(e["obec"], x + 220 - 190 * 0.85 / 2, y + 22, 190))
            casti.append(f'<text x="{x + 220}" y="{y + 262}" font-family="{NADPIS_PISMO}" font-size="46" fill="{TMAVA}" '
                         f'text-anchor="middle">{escape(e["obec"])}</text>')
            casti.append(f'<text x="{x + 220}" y="{y + 318}" font-family="{PISMO}" font-style="italic" font-size="38" '
                         f'fill="{TMAVA}" text-anchor="middle">{escape(e.get("rody", ""))}</text>')
    casti.append("</svg>")
    return "\n".join(casti)


def main():
    vstup = sys.argv[1]
    vystup = sys.argv[2] if len(sys.argv) > 2 else "dokumenty/stromy/vystup"
    koren = os.path.dirname(os.path.dirname(os.path.abspath(vstup)))
    data = json.load(open(vstup, encoding="utf-8"))
    erby_json = os.path.join(koren, "dokumenty/stromy/erby/erby.json")
    if os.path.exists(erby_json):
        for obec, z in json.load(open(erby_json, encoding="utf-8")).items():
            ERBY[obec] = os.path.abspath(os.path.join(os.path.dirname(erby_json), z["png"]))
    os.makedirs(vystup, exist_ok=True)
    jmeno = os.path.splitext(os.path.basename(vstup))[0]
    cesta_svg = os.path.join(vystup, jmeno + ".svg")
    with open(cesta_svg, "w", encoding="utf-8") as f:
        f.write(vyvod(data, koren) if data.get("typ") == "vyvod" else svg(data, koren))
    for typ in ("png", "pdf"):
        cil = os.path.join(vystup, f"{jmeno}.{typ}")
        subprocess.run(["inkscape", cesta_svg, f"--export-type={typ}", f"--export-filename={cil}"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("uloženo:", cil)


if __name__ == "__main__":
    main()
