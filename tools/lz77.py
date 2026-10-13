"""GBA BIOS LZ77 (type 0x10) decompress / compress (VRAM-safe: no 1-byte back-references).

    python -X utf8 tools/lz77.py --selftest
"""


def decompress(d, a, limit=None):
    """-> (data, compressed length) of the LZ77 block at offset a."""
    assert d[a] == 0x10, f'not LZ77 at {a:X}'
    size = d[a + 1] | d[a + 2] << 8 | d[a + 3] << 16
    if limit and size > limit:
        raise ValueError('too big')
    out = bytearray()
    i = a + 4
    while len(out) < size:
        flags = d[i]; i += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                b1, b2 = d[i], d[i + 1]; i += 2
                n = (b1 >> 4) + 3
                disp = ((b1 & 15) << 8 | b2) + 1
                if disp > len(out):
                    raise ValueError('bad back-reference')
                for _ in range(n):
                    out.append(out[-disp])
            else:
                out.append(d[i]); i += 1
    return bytes(out[:size]), i - a


def compress(data):
    """Greedy LZ77; back-reference distance >= 2 so the BIOS VRAM variant (16-bit writes) is safe too."""
    out = bytearray([0x10, len(data) & 0xFF, len(data) >> 8 & 0xFF, len(data) >> 16 & 0xFF])
    i = 0
    while i < len(data):
        flag_pos = len(out); out.append(0); flags = 0
        for bit in range(8):
            if i >= len(data):
                break
            best_n, best_d = 0, 0
            for disp in range(2, min(i, 4096) + 1):
                n = 0
                while n < 18 and i + n < len(data) and data[i + n] == data[i - disp + n]:
                    n += 1
                if n > best_n:
                    best_n, best_d = n, disp
                    if n == 18:
                        break
            if best_n >= 3:
                flags |= 0x80 >> bit
                out += bytes([(best_n - 3) << 4 | (best_d - 1) >> 8, (best_d - 1) & 0xFF])
                i += best_n
            else:
                out.append(data[i]); i += 1
        out[flag_pos] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


if __name__ == '__main__':
    import os, sys
    if '--selftest' in sys.argv:
        for data in [b'', b'abc', b'abcabcabcabcabcabc' * 50, os.urandom(3000), bytes(5000)]:
            c = compress(data)
            assert decompress(c, 0)[0] == data
        print('ok')
