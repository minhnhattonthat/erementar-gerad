import struct, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import build, romlib, vwf

# Bytes the hooks in asm/pairs.asm may change.
HOOKS = [(0x00A780, 0x00A788), (0x00A86C, 0x00A874), (0x00E5A4, 0x00E5B0), (0x00EA26, 0x00EA28),
         (0x00EA80, 0x00EA8A), (0x00EA34, 0x00EA3C), (0x02879C, 0x02879E)]


@unittest.skipUnless(romlib.ROM.exists(), 'needs rom/')
class BuildTests(unittest.TestCase):
    def test_identity_relocation(self):
        """Relocating every string with en = jp: each slot reaches the same bytes; nothing else changes."""
        orig = romlib.load()
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / 'id.gba'
            build.build(out, identity=True)
            new = out.read_bytes()
        es = build.load_entries()
        allowed = bytearray(len(orig))
        for lo, hi in HOOKS + [(build.FREE_LO, build.FREE_HI)]:
            allowed[lo:hi] = b'\1' * (hi - lo)
        for e in es:
            want = romlib.string_at(orig, int(e['id'], 16))
            for s in e['slots']:
                s = int(s, 16)
                allowed[s:s + 4] = b'\1\1\1\1'
                a = struct.unpack_from('<I', new, s)[0] - romlib.BASE
                self.assertTrue(build.FREE_LO <= a < build.FREE_HI, e['id'])
                self.assertEqual(new[a:new.index(b'\0', a)], want, e['id'])
        diff = [i for i in range(len(orig)) if orig[i] != new[i] and not allowed[i]]
        self.assertEqual(diff[:10], [])

    def test_cells(self):
        self.assertEqual(vwf.to_cells('Hi!'), [b'Hi', b'!\0'])
        self.assertEqual(vwf.to_cells('ab\ncd'), [b'ab', b'nn', b'cd'])
        self.assertEqual(vwf.to_cells('a\nb'), [b'a ', b'nn', b'b\0'])
        self.assertEqual(vwf.to_cells('Anna'), [b'An', b'na'])
        self.assertEqual(vwf.to_cells('inn'), [b'in', b'n\0'])
        self.assertEqual(vwf.to_cells('Annn'), [b'An', bytes([0x6E, vwf.ALT_N])])
        self.assertEqual(vwf.to_cells('a♪'), [b'a ', '♪'.encode('cp932')])


if __name__ == '__main__':
    unittest.main()
