"""Release gate + package: check -> build -> smoke boot -> leftover Japanese -> BPS (re-applied, verified) -> zip.

    python -X utf8 tools/release.py VERSION        e.g. 0.9   -> release/Erementar_Gerad_EN_v0.9.zip
Stops at the first failure. Never uploads anything.
"""
import hashlib, os, subprocess, sys, zipfile, zlib
from pathlib import Path
import romlib

ROOT = romlib.ROOT
# translate-retro-game skill scripts: installed by the Claude Code plugin (override with RETRO_SKILL_SCRIPTS)
SKILL = Path(os.environ.get('RETRO_SKILL_SCRIPTS') or Path.home() / '.claude' / 'plugins' / 'marketplaces' /
             'retro-translation' / 'skills' / 'translate-retro-game' / 'scripts')
PY = [sys.executable, '-X', 'utf8']


def run(cmd, what):
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        sys.exit(f'release stopped: {what} failed (exit {r.returncode})')


def hashes(data):
    return (f'{zlib.crc32(data):08X}', hashlib.md5(data).hexdigest(), hashlib.sha1(data).hexdigest())


def main(version):
    built = ROOT / 'build' / 'eg_en.gba'
    run(PY + ['tools/check.py'], 'check')
    run(PY + ['tools/build.py'], 'build')
    run(PY + [str(SKILL / 'emu.py'), str(built), '--out', 'work/qa/release_smoke', '--frames', '1800',
              '--shot-every', '300', '--smoke', '--timeout', '120'], 'smoke boot')
    run(PY + [str(SKILL / 'jp_left.py'), str(built), '--sjis', '--slots', str(built.with_suffix('.slots.txt')),
              '--known', str(built.with_suffix('.known.txt'))], 'leftover Japanese scan')
    out = ROOT / 'release'
    out.mkdir(exist_ok=True)
    name = f'Erementar_Gerad_EN_v{version}'
    bps = out / f'{name}.bps'
    run(PY + [str(SKILL / 'bps.py'), 'make', str(romlib.ROM), str(built), str(bps)], 'bps make/verify')
    orig, new = romlib.ROM.read_bytes(), built.read_bytes()
    oc, om, os_ = hashes(orig)
    nc, _, _ = hashes(new)
    readme = (ROOT / 'docs' / 'README_release.txt').read_text('utf-8').format(
        version=version, crc=oc, md5=om, sha1=os_, size=len(orig), patched_crc=nc)
    (out / 'README.txt').write_text(readme, 'utf-8', newline='\r\n')
    z = out / f'{name}.zip'
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as f:
        f.write(bps, bps.name)
        f.write(out / 'README.txt', 'README.txt')
    print(f'release ready (local only): {z}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
