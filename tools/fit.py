"""Text forms, pixel budgets and balanced wrapping (measured in-game, docs/re/font.md).

    python -X utf8 tools/fit.py "English text" [--form dlg|label|sys]   -> wrapped lines with pixel widths

Forms:
  keep   no kana/kanji, or a padded debug label: stays Japanese (debug screens, digits, symbols)
  dlg    script string shown in the dialogue box: <= 3 lines of 212 px, last line <= 200 px (page arrow)
  label  short script string without sentence punctuation (talk options, topics, place names): one line
  sys    menu/system string from rodata: same line count as the Japanese, soft target = Japanese width
English without '\\n' is wrapped by the build (balanced); an explicit '\\n' is kept as written.
"""
import re, sys
import vwf

DLG_W, DLG_LAST, DLG_LINES = 212, 200, 3
JP_RE = re.compile('[ぁ-ヿ一-鿿]')
FONT = vwf.Font()


def form(e):
    jp = e['jp']
    if not JP_RE.search(jp) or '　　　' in jp:
        return 'keep'
    if int(e['id'], 16) < 0x1F0000:
        return 'sys'
    if '\n' not in jp and len(jp) <= 10 and not re.search('[。！？…～、!?]', jp):
        return 'label'
    return 'dlg'


def jp_width(line):
    return 12 * len(line)


def limits(e):
    """(line width px, last line px, max lines, soft target px) for this entry."""
    f = form(e)
    if f == 'sys':
        lines = e['jp'].split('\n')
        w = max(jp_width(l) for l in lines)
        return DLG_W, DLG_W, len(lines), w
    if f == 'label':
        return DLG_W, DLG_W, 1, max(jp_width(e['jp']), 48)
    return DLG_W, DLG_LAST, DLG_LINES, DLG_W


def width(s):
    return FONT.text_width(s) if all(ord(c) < 0x80 for c in s) else sum(
        FONT.w[ord(c)] if ord(c) < 0x80 else vwf.SJIS_W for c in s)


def wrap(text, w=DLG_W, last=DLG_LAST, n=DLG_LINES):
    """Balanced wrap into the fewest lines (<= n) that fit; None if it can't fit."""
    words = text.split(' ')
    sp = FONT.w[ord(' ')]
    ww = [width(x) for x in words]

    def span(i, j):  # width of words[i:j] joined by spaces
        return sum(ww[i:j]) + sp * (j - i - 1)

    for k in range(1, n + 1):
        # best[j][m] = minimal max line width placing words[:j] into m lines
        INF = float('inf')
        best = [[INF] * (k + 1) for _ in range(len(words) + 1)]
        cut = [[0] * (k + 1) for _ in range(len(words) + 1)]
        best[0][0] = 0
        for m in range(1, k + 1):
            lim = last if m == k else w
            for j in range(1, len(words) + 1):
                for i in range(j):
                    if best[i][m - 1] == INF:
                        continue
                    s = span(i, j)
                    if s > lim:
                        continue
                    v = max(best[i][m - 1], s)
                    if v < best[j][m]:
                        best[j][m], cut[j][m] = v, i
        if best[len(words)][k] < INF:
            lines, j = [], len(words)
            for m in range(k, 0, -1):
                i = cut[j][m]
                lines.append(' '.join(words[i:j]))
                j = i
            return lines[::-1]
    return None


def layout(e, en=None):
    """-> (lines, error or None) for the entry's English as the build will lay it out."""
    en = e.get('en') if en is None else en
    w, last, n, _ = limits(e)
    if '\n' in en:
        lines = en.split('\n')
        if len(lines) > n:
            return lines, f'{len(lines)} lines > {n}'
        for i, l in enumerate(lines):
            lim = last if i == len(lines) - 1 else w
            if width(l) > lim:
                return lines, f'line {i + 1} is {width(l)} px > {lim}'
        return lines, None
    lines = wrap(en, w, last, n)
    if lines is None:
        return [en], f'does not fit {n} x {w} px (needs {width(en)} px)'
    return lines, None


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('text')
    ap.add_argument('--form', default='dlg', choices=['dlg', 'label', 'sys'])
    a = ap.parse_args()
    fake = {'id': '1F0000' if a.form != 'sys' else '030000', 'jp': 'あ' * 15 if a.form == 'dlg' else 'あ'}
    if a.form == 'dlg':
        fake['jp'] = 'あ。\nあ\nあ'
    lines, err = layout(fake, a.text.replace('\\n', '\n'))
    for l in lines:
        print(f'{width(l):4d} px | {l}')
    print(err or 'OK')
    sys.exit(1 if err else 0)
