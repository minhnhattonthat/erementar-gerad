"""Shared ROM helpers: paths, string reading, pointer-slot discovery (docs/re/text.md)."""
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROM = ROOT / 'rom' / '2047 - Erementar Gerad (J)(Supplex).gba'
SCRIPT_DIR = ROOT / 'script'
BASE = 0x08000000

# Where a pointer slot may live: code + rodata, skill tables, 0x1F tables, script records. Words elsewhere
# (packed data at 0x9DEE4, graphics at 0x370000-0x5CFFFF) only look like text pointers.
SLOT_REGIONS = [(0x000000, 0x03E000), (0x0B3000, 0x0BB000), (0x1F0000, 0x240000), (0x5D0000, 0x63CB7C)]
TEXT_RANGES = [(0x030000, 0x0C0000), (0x1F0000, 0x240000)]


def load(path=ROM):
    return open(path, 'rb').read()


def u32(d, a):
    return struct.unpack_from('<I', d, a)[0]


def is_lead(x):
    return 0x81 <= x <= 0x9F or 0xE0 <= x <= 0xFC


def cells(b):
    """Split string bytes into cells as the renderers do (2 bytes each, a lone last byte allowed).
    None unless every cell starts with an SJIS lead byte or printable ASCII and at least one is SJIS."""
    out = [b[i:i + 2] for i in range(0, len(b), 2)]
    if not out or not all(is_lead(c[0]) or 0x20 <= c[0] < 0x7F for c in out):
        return None
    if not any(is_lead(c[0]) for c in out):
        return None
    return out


def string_at(d, a):
    """Bytes of the NUL-terminated string at file offset a, or None if it isn't a whole text string."""
    if a <= 0 or d[a - 1] != 0 or d[a] == 0:
        return None
    e = d.find(b'\0', a)
    b = d[a:e]
    if len(b) > 1000 or not cells(b):
        return None
    try:
        b.decode('cp932')
    except UnicodeDecodeError:
        return None
    return b


def decode(b):
    return b.decode('cp932').replace('nn', '\n')


def encode_jp(s):
    return s.replace('\n', 'nn').encode('cp932')


def find_slots(d):
    """{target offset: [slot offsets]} for every aligned pointer word in SLOT_REGIONS that hits a text string."""
    out = {}
    for lo, hi in SLOT_REGIONS:
        for i in range(lo, hi, 4):
            v = u32(d, i) - BASE
            if any(a <= v < b for a, b in TEXT_RANGES) and string_at(d, v) is not None:
                out.setdefault(v, []).append(i)
    return out
