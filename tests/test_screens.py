"""Title artwork regression gates, including transparency (RGB alone cannot detect debris)."""
import hashlib
import struct
import sys
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import lz77
import romlib
import screens


@unittest.skipUnless(romlib.ROM.exists(), 'needs rom/')
class TitleLogoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = romlib.load()
        cls.pal, cls.original_tiles, cls.original_maps = screens.load(cls.rom, 'title_logo')
        tiles, maps = screens.encode(cls.rom, 'title_logo')
        # Check the compressed/decompressed assets, as consumed by the game's loader.
        cls.tiles = lz77.decompress(lz77.compress(tiles), 0)[0]
        cls.maps = [lz77.decompress(lz77.compress(m), 0)[0] for m in maps]
        assert cls.tiles == tiles and cls.maps == maps

    def test_main_logo_exact_artwork_and_transparency(self):
        """Every pixel, including every empty pixel around the outlines, is specified."""
        with Image.open(Path(__file__).parent / 'fixtures' / 'title_logo.png') as fixture:
            expected = fixture.convert('RGBA')
        idx, pals = screens.page_indices(self.tiles, self.maps[1])
        actual = screens.to_img(idx, pals, self.pal).convert('RGBA')
        actual.putalpha(Image.frombytes('L', actual.size,
                                       bytes(255 if v else 0 for row in idx for v in row)))
        self.assertEqual(actual.tobytes(), expected.tobytes(),
                         'Title differs from intended art: altered ink or leftover pixels')
        # The independently stored design, including every empty pixel outside it,
        # specifies all ink, including the taller outer Es and extended rod,
        # together with the exact original icon.
        intended = Image.new('RGBA', (240, 160), (*self.pal[32], 0))
        intended.paste(screens.title_logo_art(self.pal), screens.TITLE_LOGO_POSITION)
        icon = screens.title_logo_icon(*screens.page_indices(self.original_tiles, self.original_maps[1]),
                                       self.pal)
        intended.paste(icon, (0, 0), icon.getchannel('A'))
        self.assertEqual(actual.tobytes(), intended.tobytes(),
                         'Unexpected title pixel outside the lettering/icon, or missing/changed ink')
        design = screens.render_page(self.original_tiles, self.original_maps[1], self.pal,
                                     screens.EDITS['title_logo'][1])[0]
        self.assertEqual(actual.convert('RGB').tobytes(), design.tobytes(),
                         'Tile/palette encoding changed the intended design')

    def test_girl_and_staff_exact_original_rom_pixels(self):
        """Compare the complete icon footprint to JP art, including holes and both banks."""
        original, original_banks = screens.page_indices(self.original_tiles, self.original_maps[1])
        actual, actual_banks = screens.page_indices(self.tiles, self.maps[1])
        icon_indices = bytearray(240 * 160)
        # Independent source boundaries: do not derive the preservation test from
        # the implementation's extraction mask. These exclude all Japanese/romaji.
        for x0, y0, x1, y1 in ((108, 0, 150, 45), (113, 45, 148, 57), (40, 57, 146, 75)):
            for y in range(y0, y1):
                for x in range(x0, x1):
                    self.assertEqual(actual[y][x], original[y][x], f'Icon index changed at {x},{y}')
                    if original[y][x]:
                        old_bank, new_bank = original_banks[y // 8][x // 8], actual_banks[y // 8][x // 8]
                        self.assertEqual(new_bank, old_bank, f'Icon palette changed at {x},{y}')
                        icon_indices[y * 240 + x] = old_bank * 16 + original[y][x]
        self.assertEqual(sum(bool(v) for v in icon_indices), 2222)
        self.assertEqual(hashlib.sha256(icon_indices).hexdigest(),
                         'a331fb58cce0dd0bdbc863885be689c8c139adee11f46576c43dc7ad30c593ef')
        self.assertFalse(any(actual[y][x] for y in range(65, 71) for x in range(165, 225)),
                         'Redundant EREMENTAR GERAD caption survived')

    def test_taller_outer_es_and_full_width_rod(self):
        """All tops align; the two outer Es grow only below the common baseline."""
        idx, banks = screens.page_indices(self.tiles, self.maps[1])
        for x0, x1 in ((2, 13), (222, 236)):
            rows = [y for y in range(60) if any(idx[y][x] for x in range(x0, x1))]
            self.assertEqual((min(rows), max(rows)), (38, 59))
        for x0, x1 in ((14, 23), (24, 34), (35, 47), (48, 58), (59, 70),
                       (71, 81), (82, 93), (94, 103), (152, 166), (167, 179),
                       (180, 191), (192, 206), (207, 221)):
            # Below y=56 the preserved JP staff crosses under the left word.
            rows = [y for y in range(57) if any(idx[y][x] for x in range(x0, x1))]
            self.assertEqual((min(rows), max(rows)), (38, 55), f'Letter at {x0} is misaligned')
        self.assertFalse(any(idx[y][x] for y in range(27, 38)
                             for x in (*range(2, 104), *range(152, 236))))
        for y, ink in ((60, 1), (61, 14), (62, 4), (63, 1)):
            for x in range(146, 234):
                self.assertEqual(idx[y][x], ink, f'Broken rod/shading at {x},{y}')
                self.assertEqual(banks[y // 8][x // 8], 2)
        self.assertEqual([idx[y][234] for y in range(60, 64)], [1, 4, 4, 1])
        self.assertTrue(all(idx[y][235] == 1 for y in range(58, 64)),
                        'Rod must meet the last E with a closed dark end cap')

    def test_clean_chrome_outline_spacing_and_counters(self):
        """Heavy faces have flat chrome, continuous dark bevels and open counters."""
        idx, banks = screens.page_indices(self.tiles, self.maps[1])
        # Independent screen-coordinate specification, including the descending Es.
        bands = {y: ink for lo, hi, ink in ((39, 41, 8), (41, 43, 15), (43, 45, 8),
                                          (45, 47, 6), (47, 49, 7), (49, 51, 8),
                                          (51, 55, 15), (55, 59, 8)) for y in range(lo, hi)}
        # Exclude the original staff below y=56; it has its own exact-pixel gate.
        for x0, x1, bottom in ((2, 13, 60), (14, 103, 57), (152, 236, 60)):
            face = {(x, y) for y in range(38, bottom) for x in range(x0, x1) if idx[y][x] > 1}
            for x, y in face:
                edge = (x + 1, y) not in face or (x, y + 1) not in face
                self.assertEqual(idx[y][x], 4 if edge else bands[y],
                                 f'Broken bevel or noisy chrome at {x},{y}')
                self.assertEqual(banks[y // 8][x // 8], 2)
                self.assertTrue((x - 1, y) in face or (x + 1, y) in face,
                                f'Single-pixel face stroke at {x},{y}')
            rim = {(x + dx, y + dy) for x, y in face
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - face
            actual_rim = {(x, y) for y in range(38, bottom) for x in range(x0, x1) if idx[y][x] == 1}
            self.assertEqual(actual_rim, rim, 'Outline must be exactly one pixel thick')
        # Measure the decoded faces, independently of the glyph source: outlined
        # hairlines cannot pass by simply updating the fixture or band colours.
        for x0, x1, bottom in ((3, 12, 59), (15, 22, 55), (25, 33, 55), (36, 46, 55),
                               (49, 57, 55), (60, 69, 55), (72, 80, 55), (83, 92, 55),
                               (95, 102, 55), (153, 165, 55), (168, 178, 55),
                               (181, 190, 55), (193, 205, 55), (208, 220, 55), (223, 235, 59)):
            face = {(x, y) for y in range(39, bottom) for x in range(x0, x1) if idx[y][x] > 1}
            self.assertGreaterEqual(len(face) / ((x1 - x0) * (bottom - 39)), 0.52,
                                    f'Letter at {x0} has lost its block weight')
            for y in range(39, bottom):
                self.assertTrue(any(all((x + dx, y) in face for dx in range(3))
                                    for x in range(x0, x1 - 2)), f'Thin stroke at {x0},{y}')
        # A full transparent column separates each pair of outlined letters.
        for x in (13, 23, 34, 47, 58, 70, 81, 93, 166, 179, 191, 206, 221):
            self.assertFalse(any(idx[y][x] for y in range(38, 57 if x < 104 else 60)),
                             f'Closed letter spacing at {x}')
        # Both A counters, D's bowl and G's open mouth survive the black outline.
        for x0, y0, x1, y1 in ((87, 45, 88, 48), (199, 45, 200, 48),
                               (213, 45, 216, 49), (158, 44, 166, 46)):
            self.assertFalse(any(idx[y][x] for y in range(y0, y1) for x in range(x0, x1)),
                             f'Filled counter/aperture at {x0},{y0}')

    def test_no_isolated_pixels_or_fragments(self):
        """Neither angular spurs nor dark bevels may introduce detached debris."""
        idx, _ = screens.page_indices(self.tiles, self.maps[1])
        remaining = {(x, y) for y in range(160) for x in range(240) if idx[y][x]}
        # Face-only connectivity also catches floating chrome flecks hidden inside
        # a connected black rim. The fixture additionally gates their exact colours.
        for x0, x1 in ((2, 13), (14, 23), (24, 34), (35, 47), (48, 58), (59, 70),
                       (71, 81), (82, 93), (94, 103), (152, 166), (167, 179),
                       (180, 191), (192, 206), (207, 221), (222, 236)):
            bottom = 59 if x0 in (2, 222) else 55
            face = {(x, y) for y in range(39, bottom) for x in range(x0, x1) if idx[y][x] > 1}
            pending = [face.pop()]
            while pending:
                x, y = pending.pop()
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = x + dx, y + dy
                    if neighbor in face:
                        face.remove(neighbor)
                        pending.append(neighbor)
            self.assertFalse(face, f'Detached face/bevel fragment in letter at {x0}')
        while remaining:
            seed = remaining.pop()
            component, pending = {seed}, [seed]
            while pending:
                x, y = pending.pop()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        neighbor = x + dx, y + dy
                        if neighbor in remaining:
                            remaining.remove(neighbor)
                            component.add(neighbor)
                            pending.append(neighbor)
            self.assertGreaterEqual(len(component), 8,
                                    f'Isolated pixel/fragment at {sorted(component)}')

    def test_clear_whole_layer_before_drawing(self):
        """Even poisoned pixels outside the old glyph boxes must disappear."""
        idx, pals = screens.page_indices(self.original_tiles, self.original_maps[1])
        original = screens.to_img(idx, pals, self.pal)
        dirty = Image.new('RGB', original.size, (255, 0, 255))
        transparent = lambda x, y: self.pal[pals[y // 8][x // 8] * 16]
        icon = screens.title_logo_icon(idx, pals, self.pal)
        screens.draw_main_logo(original, transparent, self.pal, icon)
        screens.draw_main_logo(dirty, transparent, self.pal, icon)
        self.assertEqual(dirty.tobytes(), original.tobytes())

    def test_approved_subtitle_pixel_identical(self):
        """Hashes captured from the working tree's approved third map before this redesign."""
        idx, pals = screens.page_indices(self.tiles, self.maps[2])
        rgb = screens.to_img(idx, pals, self.pal).tobytes()
        indices = bytes(v for row in idx for v in row)
        self.assertEqual(hashlib.sha256(rgb).hexdigest(),
                         '669aea112a1cc7333fb5ff90e6744f678b3c7d2e341120c9a2ef470841692652')
        self.assertEqual(hashlib.sha256(indices).hexdigest(),
                         'fa085a3b3d6ff7574fefcdaf0053e92c37c7833e60820a5924a143a56feb6e88')

    def test_background_and_asset_limits(self):
        original = screens.to_img(*screens.page_indices(self.original_tiles, self.original_maps[0]), self.pal)
        actual = screens.to_img(*screens.page_indices(self.tiles, self.maps[0]), self.pal)
        self.assertEqual(actual.tobytes(), original.tobytes())
        # Stay within the original title's allocation, not just the 10-bit map ceiling.
        self.assertLessEqual(len(self.tiles), len(self.original_tiles))
        original_at = screens.ptr(self.rom, 0x0181CC)
        _, packed_size = lz77.decompress(self.rom, original_at)
        self.assertLessEqual(len(lz77.compress(self.tiles)), packed_size)
        for new, old in zip(self.maps, self.original_maps):
            self.assertEqual(len(new), 0x500)
            self.assertEqual(len(new), len(old))
            self.assertLessEqual(len(lz77.compress(new)), len(lz77.compress(old)))
            self.assertTrue(all((entry[0] & 0x3ff) < len(self.tiles) // 32
                                for entry in struct.iter_unpack('<H', new)))


if __name__ == '__main__':
    unittest.main()
