import json, re, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import romlib

# Japanese-looking runs in text ranges that no pointer reaches, on purpose:
KNOWN_UNREACHED = [
    (0x0386B4, 0x0386BB), (0x03C598, 0x03C59F), (0x03CC00, 0x03CC17), (0x03CF18, 0x03CF2F),  # unused rodata
    (0x1F1A9F, 0x1F2018),  # font character map (code order), data
    (0x0B1000, 0x0B3000), (0x1F0000, 0x1F1A9F), (0x23D600, 0x240000),  # graphics/data bytes
]


@unittest.skipUnless(romlib.ROM.exists(), 'needs rom/')
class TextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = romlib.load()
        cls.es = [e for p in sorted(romlib.SCRIPT_DIR.glob('*.json')) for e in json.loads(p.read_text('utf-8'))]

    def test_roundtrip(self):
        for e in self.es:
            a = int(e['id'], 16)
            self.assertEqual(romlib.encode_jp(e['jp']), romlib.string_at(self.d, a), e['id'])

    def test_dump_matches_rom(self):
        slots = romlib.find_slots(self.d)
        self.assertEqual({'%06X' % t for t in slots}, {e['id'] for e in self.es})
        for e in self.es:
            self.assertEqual(['%06X' % s for s in sorted(slots[int(e['id'], 16)])], e['slots'], e['id'])

    def test_coverage(self):
        covered = bytearray(len(self.d))
        for e in self.es:
            a = int(e['id'], 16)
            covered[a:a + len(romlib.encode_jp(e['jp']))] = b'\1' * len(romlib.encode_jp(e['jp']))
        pat = re.compile(rb'(?:[\x81-\x9f\xe0-\xfc][\x40-\x7e\x80-\xfc]){3,}')
        miss = []
        for lo, hi in [(0x038000, 0x03E000), (0x0B3000, 0x0BB000), (0x1F0000, 0x23D600)]:
            for m in pat.finditer(self.d, lo, hi):
                a, b = m.span()
                if any(covered[a:b]) or any(x <= a < y for x, y in KNOWN_UNREACHED):
                    continue
                try:
                    t = self.d[a:b].decode('cp932')
                except UnicodeDecodeError:
                    continue
                if re.search('[ぁ-ヿ]', t):
                    miss.append('%06X %s' % (a, t))
        self.assertEqual(miss, [])


if __name__ == '__main__':
    unittest.main()
