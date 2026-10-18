"""Title QA crops and lettering comparison: python tools/logo_compare.py work/qa/logo7."""
from pathlib import Path
import sys

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import lz77
import romlib
import screens

out = ROOT / sys.argv[1]
with Image.open(out / 'final.png') as shot:
    shot.crop((0, 0, 240, 116)).resize((960, 464), Image.Resampling.NEAREST).save(out / 'logo-zoom.png')

with Image.open(ROOT / 'work/ref/anime_logo.png') as source:
    left = source.convert('RGB').crop((12, 146, 481, 254))
    right = source.convert('RGB').crop((604, 146, 957, 254))
# Exclude the reference's staff/underline below the ordinary letters; retain
# both descending outer Es. The middle character is outside these two crops.
ImageDraw.Draw(left).rectangle((72, 94, left.width, left.height), fill='white')
ImageDraw.Draw(left).rectangle((440, 0, left.width, 60), fill='white')
ImageDraw.Draw(right).rectangle((0, 0, right.width, 10), fill='white')
ImageDraw.Draw(right).rectangle((0, 0, 12, 22), fill='white')
ImageDraw.Draw(right).rectangle((0, 95, 282, right.height), fill='white')
reference = Image.new('RGB', (left.width + right.width + 26, 108), 'white')
reference.paste(left, (0, 0))
reference.paste(right, (left.width + 26, 0))
reference = reference.resize((round(reference.width * 88 / 108), 88), Image.Resampling.LANCZOS)

built = (ROOT / 'build/eg_en.gba').read_bytes()
palette, tiles, maps = screens.load(built, 'title_logo')
idx, banks = screens.page_indices(tiles, maps[1])
logo = screens.to_img(idx, banks, palette).convert('RGBA')
logo.putalpha(Image.frombytes('L', logo.size, bytes(255 if v else 0 for row in idx for v in row)))
new = Image.new('RGB', (193, 22), 'white')
for box, x in (((2, 38, 103, 60), 0), ((152, 38, 236, 60), 109)):
    word = logo.crop(box)
    new.paste(word, (x, 0), word.getchannel('A'))
# The preserved left staff crosses below ordinary letters, outside their baseline.
ImageDraw.Draw(new).rectangle((11, 18, 100, 21), fill='white')
new = new.resize((772, 88), Image.Resampling.NEAREST)
comparison = Image.new('RGB', (1540, 164), 'white')
draw = ImageDraw.Draw(comparison)
draw.text((20, 12), 'Official reference - lettering only', fill='black')
draw.text((750, 12), 'New lettering - decoded built ROM, 4x nearest-neighbour', fill='black')
comparison.paste(reference, (20, 42))
comparison.paste(new, (750, 42))
draw.text((20, 148), 'Both lettering samples are 88 px high; centre artwork and staff omitted.', fill='black')
comparison.save(out / 'compare.png')

rom = romlib.load()
_, original_tiles, original_maps = screens.load(rom, 'title_logo')
print('Title tiles:', len(tiles) // 32, '/', len(original_tiles) // 32)
print('Compressed title tiles:', len(lz77.compress(tiles)))
print('Map raw sizes:', [len(m) for m in maps])
print('Compressed map sizes:', [len(lz77.compress(m)) for m in maps])
