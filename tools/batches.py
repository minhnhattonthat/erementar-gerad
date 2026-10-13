"""Translator batches (docs/translator-brief.md).

    python -X utf8 tools/batches.py split [--size 3500]   -> work/tl/bNNN.tsv + work/tl/bNNN.terms.txt
    python -X utf8 tools/batches.py check bNNN            -> validates work/tl/bNNN.out.tsv; prints OK
    python -X utf8 tools/batches.py merge bNNN [...]      -> check, then write en into script/*.json
    python -X utf8 tools/batches.py status

Input TSV: id, speaker, form, limit, jp (' / ' between the Japanese lines). Output TSV: id<TAB>English.
`split` only takes untranslated entries and never rewrites a batch file that exists (delete it to re-split).
"""
import json, struct, sys
import fit, lint, romlib

TL = romlib.ROOT / 'work' / 'tl'
# Speaker id = byte +8 of a dialogue record (string pointer at +0x10, byte +0xC = 0xFF). Names from context.
SPEAKERS = {0: 'narration/none', 1: 'Coud', 2: 'Ren', 3: 'Rowen', 4: 'Kea', 5: 'Cisqua',
            6: '??? (spiky-haired Pledger, prologue silhouette)', 7: "??? (his Edel Raid, ends lines '-no yo')",
            8: 'travelling merchant (Kansai dialect)', 9: 'timid girl (Chiruru?)', 10: 'arena official',
            11: 'Arc Aile Porto Galeon branch member', 12: 'townsman', 13: "shop lady (innkeeper's twin sister)",
            14: 'old fisherman', 15: 'priest', 16: 'thug leader', 17: "??? (Edel Raid, '-no yo')",
            18: 'grieving woman', 19: 'innkeeper (okami)', 20: 'Arc Aile officer'}


def speaker(d, e):
    for s in e['slots']:
        s = int(s, 16)
        if 0x5D0000 <= s < 0x63CB7C and d[s - 0x10 + 0xC] == 0xFF:
            n = d[s - 0x10 + 8]
            return SPEAKERS.get(n, f'NPC#{n}')
    return ''


def all_entries():
    out = []
    for p in sorted(romlib.SCRIPT_DIR.glob('*.json')):
        out += [(p, e) for e in json.loads(p.read_text('utf-8'))]
    return out


def limit_text(e):
    w, last, n, soft = fit.limits(e)
    f = fit.form(e)
    if f == 'dlg':
        return f'{n}x{w}px'
    return f'{n}x{soft}px'


def split(size):
    TL.mkdir(parents=True, exist_ok=True)
    d = romlib.load()
    gloss = lint.glossary()
    todo = [e for _, e in all_entries() if fit.form(e) != 'keep' and e.get('en') is None]
    batches, cur, n = [], [], 0
    for e in todo:
        cur.append(e)
        n += len(e['jp'])
        if n >= size:
            batches.append(cur)
            cur, n = [], 0
    if cur:
        batches.append(cur)
    k = 0
    taken = {line.split('\t')[0] for p in TL.glob('b[0-9][0-9][0-9].tsv') for line in p.read_text('utf-8').splitlines()}
    made = 0
    for b in batches:
        b = [e for e in b if e['id'] not in taken]
        if not b:
            continue
        name = f'b{k:03d}'
        while (TL / f'{name}.tsv').exists():
            k += 1
            name = f'b{k:03d}'
        rows = [f"{e['id']}\t{speaker(d, e)}\t{fit.form(e)}\t{limit_text(e)}\t{e['jp'].replace(chr(10), ' / ')}" for e in b]
        (TL / f'{name}.tsv').write_text('\n'.join(rows) + '\n', 'utf-8', newline='\n')
        write_terms(name, [e['jp'] for e in b], gloss)
        made += 1
        k += 1
    print(f'{made} batches written to {TL}')


def write_terms(name, jps, gloss):
    terms = [f'{jp} | {en}' + (f' | avoid: {", ".join(av)}' if av else '')
             for jp, en, av in gloss if any(jp in j for j in jps)]
    (TL / f'{name}.terms.txt').write_text('\n'.join(terms) + '\n', 'utf-8', newline='\n')


def refresh_terms():
    """Rewrite every bNNN.terms.txt from the current glossary.md."""
    gloss = lint.glossary()
    for p in sorted(TL.glob('b[0-9][0-9][0-9].tsv')):
        write_terms(p.stem, [line.split('\t')[4] for line in p.read_text('utf-8').splitlines() if line], gloss)


def read_out(name):
    p = TL / f'{name}.out.tsv'
    out = {}
    for i, line in enumerate(p.read_text('utf-8-sig').splitlines()):
        if not line.strip():
            continue
        if '\t' not in line:
            raise SystemExit(f'{p.name}:{i + 1}: no TAB')
        k, v = line.split('\t', 1)
        if k in out:
            raise SystemExit(f'{p.name}:{i + 1}: duplicate id {k}')
        out[k.strip()] = v.replace('\\n', '\n').strip()
    return out


def check(name, quiet=False):
    ids = [line.split('\t')[0] for line in (TL / f'{name}.tsv').read_text('utf-8').splitlines() if line]
    out = read_out(name)
    ents = {e['id']: e for _, e in all_entries()}
    gloss = lint.glossary()
    errs = []
    if set(out) != set(ids):
        errs += [f'missing id {i}' for i in ids if i not in out] + [f'extra id {i}' for i in out if i not in ids]
    for i in ids:
        if i in out:
            if not out[i]:
                errs.append(f'{i}: empty')
                continue
            e, _ = lint.check_entry(ents[i], out[i], gloss)
            errs += [f'{i}: {x}' for x in e]
    for x in errs:
        print(x)
    if not quiet:
        print('OK' if not errs else f'{len(errs)} errors')
    return not errs, out


def merge(names):
    for name in names:
        ok, out = check(name, quiet=True)
        if not ok:
            raise SystemExit(f'{name}: fix the errors above first')
        for p in sorted(romlib.SCRIPT_DIR.glob('*.json')):
            es = json.loads(p.read_text('utf-8'))
            hit = False
            for e in es:
                if e['id'] in out:
                    e['en'] = out[e['id']]
                    hit = True
            if hit:
                with open(p, 'w', encoding='utf-8', newline='\n') as f:
                    json.dump(es, f, ensure_ascii=False, indent=1)
                    f.write('\n')
        print(f'{name}: merged {len(out)}')


def status():
    es = [e for _, e in all_entries() if fit.form(e) != 'keep']
    print(f'{sum(e.get("en") is not None for e in es)}/{len(es)} translated')
    for p in sorted(TL.glob('b[0-9][0-9][0-9].tsv')):
        o = p.with_name(p.stem + '.out.tsv')
        print(p.stem, 'out' if o.exists() else '-')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if cmd == 'split':
        split(int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 3500)
    elif cmd == 'check':
        sys.exit(0 if check(sys.argv[2])[0] else 1)
    elif cmd == 'merge':
        merge(sys.argv[2:])
    elif cmd == 'terms':
        refresh_terms()
    else:
        status()
