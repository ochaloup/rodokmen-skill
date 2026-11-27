#!/usr/bin/env python3
"""Příběhy osob (data/pribehy_osob.md) a jejich otisky dat.

Každý oddíl má hlavičku „## <číslo> Jméno <!-- otisk:xxxxxxxx -->“. Otisk shrnuje údaje osoby, jejích rodičů, partnera,
dítěte v linii a bočních příbuzných. Když se data změní, příběh je „zastaralý“ a musí se zkontrolovat.

Použití:
  pribehy.py stav                 zastaralé příběhy, osoby bez příběhu, roky v příběhu, které v datech nejsou
                                  (ověřené z jiného zdroje zapsat do oddílu: <!-- roky ověřeny: 1791 1812 (rodinná kniha) -->)
  pribehy.py otisk <č.> [<č.> …]  po kontrole příběhu zapíše aktuální otisk (all = všem)
  pribehy.py podklady <výstup.md> <č.> [<č.> …]   podklady pro psaní příběhů (data osoby, rodina, zápisy, odkazy)
  pribehy.py rod <č. rodu 8–15>   vypíše čísla osob rodu, které příběh mají mít
"""
import hashlib, json, os, re, sys
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
FILE = os.path.join(DATA, "pribehy_osob.md")
HEAD = re.compile(r"^## +(\d+)\b([^\n]*?)(?: *<!-- *otisk:([0-9a-f]+) *-->)? *$", re.M)


def load():
    ns = {}
    exec(open(os.path.join(DATA, "osoby.py"), encoding="utf-8").read(), ns)
    zaz = json.load(open(os.path.join(DATA, "zaznamy.json"), encoding="utf-8"))
    return ns["P"], ns.get("SIDE", []), ns.get("SAME", {}), {z["klic"]: z for z in zaz}


def eligible(k, p, SAME):
    """Osoba má mít příběh: ne žijící, ne prázdné místo, ne druhý výskyt téže osoby."""
    if k in SAME or p.get("n", "").startswith(("otec neuveden", "matka neuvedena")) or p.get("n") in ("", "?"):
        return False
    return "Žijící" not in p.get("note", "")


def dossier(k, P, SIDE):
    def pick(n):
        q = P.get(n)
        return None if q is None else {x: q.get(x) for x in ("n", "y", "st", "f", "r", "note") if q.get(x)}
    return dict(osoba=pick(k), otec=pick(2 * k), matka=pick(2 * k + 1),
                partner=pick(k ^ 1) if k > 1 else None, dite_v_linii=pick(k // 2) if k > 1 else None,
                bocni=[{x: s.get(x) for x in ("n", "t")} for s in SIDE if s.get("k") == k])


def otisk(k, P, SIDE):
    return hashlib.sha1(json.dumps(dossier(k, P, SIDE), ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:10]


def sections(text):
    """[(číslo, otisk nebo None, start hlavičky, konec hlavičky, konec oddílu)]"""
    heads = list(HEAD.finditer(text))
    return [(int(m.group(1)), m.group(3), m.start(), m.end(), heads[i + 1].start() if i + 1 < len(heads) else len(text))
            for i, m in enumerate(heads)]


def stale(P, SIDE):
    """Pro kontrola.py a export_web.py: seznam (číslo, jméno) příběhů, jejichž otisk nesedí s daty."""
    if not os.path.exists(FILE):
        return []
    text = open(FILE, encoding="utf-8").read()
    return [(k, P.get(k, {}).get("n", "?")) for k, o, *_ in sections(text) if k not in P or o != otisk(k, P, SIDE)]


def years_check(k, body, P, SIDE, recs):
    d = dossier(k, P, SIDE)
    known = json.dumps(d, ensure_ascii=False) + json.dumps(P.get((k // 2) ^ 1, {}), ensure_ascii=False)
    for r in (P.get(k, {}).get("r") or []):
        known += recs.get(r, {}).get("shrnuti", "") + recs.get(r, {}).get("datum", "")
    ok = " ".join(re.findall(r"<!-- *roky ověřeny:([^>]*)-->", body))
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    return sorted({y for y in re.findall(r"(?<!\d)(1[5-9]\d\d|20[0-2]\d)(?!\d)", body) if y not in known and y not in ok})


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    P, SIDE, SAME, recs = load()
    text = open(FILE, encoding="utf-8").read() if os.path.exists(FILE) else ""
    secs = sections(text)
    if a[0] == "stav":
        have = {s[0] for s in secs}
        for k, o, _, he, end in secs:
            if k not in P:
                print(f"CHYBA: příběh {k} – osoba v osoby.py není")
                continue
            if o != otisk(k, P, SIDE):
                print(f"ZKONTROLOVAT: {k} {P[k]['n']} – data se změnila (nebo chybí otisk)")
            bad = years_check(k, text[he:end], P, SIDE, recs)
            if bad:
                print(f"OVĚŘIT ROKY: {k} {P[k]['n']} – v datech nejsou: {', '.join(bad)}")
        missing = [k for k, p in sorted(P.items()) if eligible(k, p, SAME) and k not in have]
        print(f"{len(secs)} příběhů; bez příběhu {len(missing)} osob" + (f": {' '.join(map(str, missing[:40]))}{' …' if len(missing) > 40 else ''}" if missing else ""))
    elif a[0] == "otisk":
        want = None if a[1:] == ["all"] else {int(x) for x in a[1:]}
        out, last = [], 0
        for k, o, hs, he, _ in secs:
            out.append(text[last:hs])
            name = HEAD.match(text, hs).group(2).strip()
            new = otisk(k, P, SIDE) if (want is None or k in want) and k in P else o
            out.append(f"## {k} {name}" + (f" <!-- otisk:{new} -->" if new else ""))
            last = he
        out.append(text[last:])
        open(FILE, "w", encoding="utf-8").write("".join(out))
        print("otisk zapsán:", "všem" if want is None else " ".join(map(str, sorted(want))))
    elif a[0] == "podklady":
        dst, ks = a[1], [int(x) for x in a[2:]]
        slugs = json.load(open(os.path.join(ROOT, "web", "src", "data", "site.json"), encoding="utf-8")).get("people", {})
        by_k = {v["k"]: s for s, v in slugs.items()}
        parts = []
        for k in ks:
            d = dossier(k, P, SIDE)
            rel = {n: by_k.get(n) for n in (k, 2 * k, 2 * k + 1, k ^ 1, k // 2) if by_k.get(n)}
            z = {r: dict(datum=recs[r].get("datum"), nazev=recs[r].get("nazev"), shrnuti=recs[r].get("shrnuti"))
                 for r in (P[k].get("r") or []) if r in recs}
            parts.append(f"# {k}\n\nodkazy (číslo → /osoba/<adresa>/): {json.dumps(rel, ensure_ascii=False)}\n\n"
                         f"data: {json.dumps(d, ensure_ascii=False, indent=1)}\n\nzápisy: {json.dumps(z, ensure_ascii=False, indent=1)}\n")
        open(dst, "w", encoding="utf-8").write("\n".join(parts))
        print(f"{len(ks)} osob → {dst}")
    elif a[0] == "rod":
        r = int(a[1])
        have = {s[0] for s in secs}
        ks = [k for k, p in sorted(P.items()) if k >= 8 and eligible(k, p, SAME) and k >> (k.bit_length() - 4) == r and k not in have]
        print(len(ks), " ".join(map(str, ks)))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
