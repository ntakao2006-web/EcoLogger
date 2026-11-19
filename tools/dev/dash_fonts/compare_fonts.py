#!/usr/bin/python3
"""車載画面DASHの数字の書体の候補を、本物のDASHの描き方で描いて見比べる（SP-12-2）。

WSLなど、cairo・Pangoのある所で動かす（python3-gi-cairo が要る）。候補の書体は ~/.fonts に置いておく
（置いていない書体は飛ばす）。出すもの：
  <out>/<名前>-normal.png・-warn3.png   その書体で描いたDASH（1280x800）
  <out>/sheet.png                        全部の候補を並べた一覧
  <out>/result.txt                       数字が等幅か、桁の幅、今の周の数字の縮み具合

  python3 tools/dev/dash_fonts/compare_fonts.py outputs/dash_fonts_20261119
"""
import sys
from pathlib import Path

import cairo
import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'RaceCapture-UNOQ'))
import ecocapture_dash as dash  # noqa: E402
from dash_model import load_config, rpm_segments, segment_colours  # noqa: E402

# (ファイル名に使う名前, 一覧に出す名前, 書体の名前, 太さ, 可変書体の指定, 細い線用の指定, 配る条件)
CANDIDATES = [
    ('bahnschrift', 'Bahnschrift（見本の書体。Windowsのもので本体へは配れない）', 'Bahnschrift', 500, 'wdth=88,wght=500', 'wdth=88,wght=300', '配れない'),
    ('dejavu', 'DejaVu Sans Bold（いま本体にある書体）', 'DejaVu Sans', 700, None, None, '本体にある'),
    ('barlow-semi', 'Barlow Semi Condensed Medium', 'Barlow Semi Condensed', 500, None, None, 'OFL'),
    ('barlow-semi-600', 'Barlow Semi Condensed SemiBold', 'Barlow Semi Condensed', 600, None, None, 'OFL'),
    ('barlow-cond', 'Barlow Condensed SemiBold', 'Barlow Condensed', 600, None, None, 'OFL'),
    ('sofia-semi', 'Sofia Sans Semi Condensed 600', 'Sofia Sans Semi Condensed', 600, 'wght=600', 'wght=300', 'OFL'),
    ('saira-semi', 'Saira SemiCondensed Medium', 'Saira SemiCondensed', 500, None, None, 'OFL'),
    ('roboto-cond', 'Roboto Condensed 600', 'Roboto Condensed', 600, 'wght=600', 'wght=300', 'OFL'),
    ('plex-cond', 'IBM Plex Sans Condensed SemiBold', 'IBM Plex Sans Condensed', 600, None, None, 'OFL'),
    ('oswald', 'Oswald 500', 'Oswald', 500, 'wght=500', 'wght=300', 'OFL'),
    ('b612', 'B612 Bold（旅客機の計器用に作られた書体）', 'B612', 700, None, None, 'OFL'),
]
W, H = 1280, 800


def render(painter, config, state_name):
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surface)
    dash.paint(ctx, painter, dash.fixed_state(config, state_name), float(W), segment_colours(rpm_segments(config)), 0.0)
    return surface


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    config = load_config('/nonexistent')
    have = {family.get_name() for family in PangoCairo.FontMap.get_default().list_families()}
    done, lines = [], []
    for key, title, family, weight, variations, thin, licence in CANDIDATES:
        if family not in have:
            lines.append(f'{title}: この機械に無いので飛ばした')
            continue
        dash.NUM_FONTS = ((family, weight, variations, thin),)
        painter = dash.Painter(Pango, PangoCairo)
        shots = {}
        for state_name in ('normal', 'warn3'):
            shots[state_name] = render(painter, config, state_name)
            shots[state_name].write_to_png(str(out / f'{key}-{state_name}.png'))
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_RGB24, 10, 10))
        widths = [painter.width(ctx, digit, 100) for digit in '0123456789']
        lap = painter.width(ctx, '1:52.34', 100)
        column = (W - 48) / 3 - 20
        lines.append(f'{title} [{licence}]: 数字の幅 {min(widths):.1f}〜{max(widths):.1f}（100pxの字で）'
                     f'{"＝等幅" if max(widths) - min(widths) < 0.5 else "＝幅が違う"}、'
                     f'周のタイム「1:52.34」の幅 {lap:.0f}（枠 {column:.0f}。'
                     f'{"収まる" if lap <= column else f"{column / lap * 100:.0f}%に縮む"}）、'
                     f'回転数「8888」の幅 {painter.width(ctx, "8888", 48):.0f}（48pxの字で）')
        done.append((title, licence, shots['normal']))
    (out / 'result.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    # the sheet: two across, each screen at half size under its name
    dash.NUM_FONTS = (('DejaVu Sans', 700, None, None),)
    label = dash.Painter(Pango, PangoCairo)
    cell_w, cell_h, head, pad = W // 2, H // 2, 44, 16
    rows = (len(done) + 1) // 2
    sheet = cairo.ImageSurface(cairo.FORMAT_RGB24, 2 * cell_w + 3 * pad, rows * (cell_h + head + pad) + pad)
    ctx = cairo.Context(sheet)
    ctx.set_source_rgb(0.11, 0.11, 0.11)
    ctx.paint()
    for k, (title, licence, shot) in enumerate(done):
        x, y = pad + (k % 2) * (cell_w + pad), pad + (k // 2) * (cell_h + head + pad)
        label.text(ctx, x, y + 30, 22, f'{k + 1}  {title}', '#f2f2f2', jp=True)
        ctx.save()
        ctx.translate(x, y + head)
        ctx.scale(0.5, 0.5)
        ctx.set_source_surface(shot, 0, 0)
        ctx.paint()
        ctx.restore()
    sheet.write_to_png(str(out / 'sheet.png'))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
