"""Dump every pointer-reached string to script/*.json (docs/re/text.md).

    python -X utf8 tools/dump.py [--force]

Never clobbers English: without --force it refuses if script/ has files; with --force it keeps every existing
`en`/`notes` by id.
"""
import json, sys
import romlib

CHUNK = 200


def entries(d):
    slots = romlib.find_slots(d)
    out = []
    for t, ss in slots.items():
        out.append({'id': '%06X' % t, 'jp': romlib.decode(romlib.string_at(d, t)), 'en': None,
                    'slots': ['%06X' % s for s in sorted(ss)]})
    return out


def files(d):
    """{filename: [entries]}: sys = rodata strings, ev_NNN = script strings in order of first slot."""
    es = entries(d)
    sysl = sorted((e for e in es if int(e['id'], 16) < 0x1F0000), key=lambda e: int(e['id'], 16))
    ev = sorted((e for e in es if int(e['id'], 16) >= 0x1F0000), key=lambda e: int(e['slots'][0], 16))
    out = {'sys.json': sysl}
    for i in range(0, len(ev), CHUNK):
        out['ev_%03d.json' % (i // CHUNK)] = ev[i:i + CHUNK]
    return out


def write(path, es):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(es, f, ensure_ascii=False, indent=1)
        f.write('\n')


def main():
    force = '--force' in sys.argv
    romlib.SCRIPT_DIR.mkdir(exist_ok=True)
    old = {}
    existing = list(romlib.SCRIPT_DIR.glob('*.json'))
    if existing and not force:
        sys.exit('script/ has files; refusing to overwrite (use --force to re-dump keeping en/notes)')
    for p in existing:
        for e in json.loads(p.read_text('utf-8')):
            old[e['id']] = e
    n = 0
    for name, es in files(romlib.load()).items():
        for e in es:
            o = old.get(e['id'], {})
            for k in ('en', 'notes'):
                if o.get(k) is not None:
                    e[k] = o[k]
        write(romlib.SCRIPT_DIR / name, es)
        n += len(es)
    print(f'{n} strings')


if __name__ == '__main__':
    main()
