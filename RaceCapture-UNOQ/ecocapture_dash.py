#!/usr/bin/python3
"""EcoCapture DASH: the driver screen on the UNO Q's HDMI (Xorg :2), drawn from EcoCapture's telemetry.

Runs as ecocapture-dash.service in place of the RaceCapture app: the two units conflict, so
starting one stops the other (dash_switch.sh). Acquisition, eMMC/SD recording and RCP are not
touched; the EcoCapture admin window underneath is paused as touch_launcher.py does. What is
shown is worked out in dash_model.py. Settings: ~/.config/ecocapture-dash.json (dash_model.DEFAULTS).

  ecocapture_dash.py                    the dash
  ecocapture_dash.py --demo             a made-up drive (laps, the gap, a pit stop, oil heating up to 130 C,
                                        two oil pressure drops: one alone, one with the temperatures)
  ecocapture_dash.py --state warn       one fixed screen: normal slower start pit pitbox pitlane shift limit warn
                                        warnpress warn2 warn3 lost stale sendwait sendoff (warn2: oil pressure
                                        + oil, warn3: all three warnings; pitlane: 63 km/h after the line in
                                        the pit lane; sendwait: sending on but nothing going out, sendoff: off)
  ecocapture_dash.py --sound warn       play the warning sound once and exit (--volume 0.3)
  --size 1920x1080 --snapshot out.png   window size; --snapshot paints the screen into a PNG and exits
                                        (no window; --flash-dark: the dark half of the flashing)
  --no-pause                            leave the other display apps alone (checking on a running UNO Q)
"""
from __future__ import annotations

import argparse
import atexit
import json
import math
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dash_model import DashModel, load_config, rpm_segments, segment_colours, tone_wav  # noqa: E402

CONFIG_PATH = Path.home() / '.config' / 'ecocapture-dash.json'
LAPREF_PATH = Path.home() / '.cache' / 'ecocapture-dash' / 'lapref.json'
# The fonts, the first the machine has. Numbers: Bahnschrift (a DIN, on a Windows PC only: what the
# mock-up was drawn with, for checking there); the UNO Q has DejaVu Sans until a DIN that may be shipped is
# chosen and put first here. (family, weight, variable-font settings, the same for the thin dashes)
NUM_FONTS = (('Bahnschrift', 500, 'wdth=88,wght=500', 'wdth=88,wght=300'), ('DejaVu Sans', 700, None, None))
TEXT_FONTS = (('Noto Sans CJK JP', 500), ('Yu Gothic UI', 600), ('DejaVu Sans', 700))
DESIGN_W, DESIGN_H = 1280.0, 800.0  # the mock-up's canvas (docs/design/dash_mock_simple_20261119.html)
GREEN, YELLOW, RED, BLUE = '#2fc64c', '#f2c418', '#ec3030', '#3b9dff'
WHITE, UNIT, GREY, DIM, OFF = '#f2f2f2', '#bdbdbd', '#8a8a8a', '#555555', '#262626'
PLATE_RED = '#e01414'
SEG = {'g': GREEN, 'y': YELLOW, 'r': RED}
SEG_DARK = '#3a0606'
SEG_FILL = 0.893  # a segment's width over its pitch (the gap is the rest), as the 30-segment bar had
WARN_SCALE = {1: 1.0, 2: 0.75, 3: 0.55}  # the warnings in the band, by how many are on (they share its width)
FLASH_PERIOD_S = 0.5  # bright and dark red twice a second while flashing (under 3 a second: photosensitivity)


class Sound:
    """Plays the warning WAVs with aplay (on the UNO Q: HDMI to the monitor's speaker). A new warning
    while one is sounding starts it again from the top (as the phone's circuit screen does), so the
    ear hears that something more has come."""

    def __init__(self, config):
        self.config = config['sound']
        self.proc = None
        for control in self.config.get('route', []) if self.config.get('enabled', True) else []:
            # the mixer path to the speaker (dash_model.DEFAULTS)
            try:
                subprocess.run(['amixer', '-q', '-c', self.config.get('card', '0'), 'cset', f'name={control}', '1'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            except (OSError, subprocess.SubprocessError):
                pass
        self.folder = Path(tempfile.mkdtemp(prefix='ecocapture-dash-'))
        atexit.register(shutil.rmtree, self.folder, True)
        self.files = {}
        for kind in ('warn',):
            path = self.folder / f'{kind}.wav'
            path.write_bytes(tone_wav(kind, self.config.get('volume', 0.8), repeat=self.config.get('repeat', 6)))
            self.files[kind] = path

    def play(self, kind):
        if not self.config.get('enabled', True) or kind not in self.files:
            return None
        if self.proc and self.proc.poll() is None:  # still sounding: from the top again
            self.proc.terminate()
            try:
                self.proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        command = [part.format(device=self.config.get('device', 'default'), file=self.files[kind])
                   for part in self.config.get('command', ['aplay', '-q', '-D', '{device}', '{file}'])]
        try:
            self.proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            self.proc = None
        return self.proc


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=1.0) as response:
            return json.loads(response.read())
    except (OSError, ValueError):
        return None


class DemoFeed:
    """A made-up drive on a 2.5 km circle (not a real course): laps of about 1:53, the oil
    heating from 95 C to 133 C over eight minutes, a pit lap every seventh lap, and in every ten minutes
    two six-second oil pressure drops (at 200 s alone, at 440 s with the oil and water over their limits)."""
    LAT0, LON0, RADIUS = 38.14, 140.77, 400.0

    def __init__(self, start):
        self.t0 = start

    @staticmethod
    def lap_s(k):
        return 2 * math.pi * DemoFeed.RADIUS / (22.2 * (1 + .015 * math.sin(1.3 * k + 2.5)))

    def frame(self, now):
        t = now - self.t0 - 5.0  # five seconds waiting for the start
        lap = {'CurrentLap': 0, 'LapCount': 0, 'ElapsedTime': None, 'LapTime': None, 'BestLap': None,
               'RaceTime': None, 'LapDiffS': None, 'LastLapPit': None}
        lat, lon = self.LAT0 - self.RADIUS / 111320.0, self.LON0
        if t >= 0:
            k, begin, times = 1, 0.0, []
            while begin + self.lap_s(k) <= t:
                times.append(self.lap_s(k)); begin += self.lap_s(k); k += 1
            into = t - begin
            angle = 2 * math.pi * into / self.lap_s(k) - math.pi / 2
            lat = self.LAT0 + self.RADIUS * math.sin(angle) / 111320.0
            lon = self.LON0 + self.RADIUS * math.cos(angle) / (111320.0 * math.cos(math.radians(self.LAT0)))
            pit = lambda n: n % 7 in (0, 1) and n > 1
            lap.update(CurrentLap=k, LapCount=k - 1, ElapsedTime=into / 60, RaceTime=t / 60, LapStartPit=pit(k) and pit(k - 1))
            quarter = int(4 * into / self.lap_s(k))  # four sectors of a quarter lap each
            if quarter or times:
                lap.update(Sector=quarter + 1, LastSector=quarter or 4, SectorDiffS=round(0.4 * math.sin(1.7 * k + quarter), 2))
            if times:
                lap.update(LapTime=times[-1] / 60, BestLap=min(times) / 60, LastLapPit=pit(k - 1))
                if len(times) >= 2 and not pit(k - 1) and not pit(k - 2):
                    lap['LapDiffS'] = round(times[-1] - times[-2], 3)
        cycle = (now - self.t0) % 600
        oil = 95 + 38 * cycle / 480 if cycle < 480 else 133 - 30 * (cycle - 480) / 120
        # pulling through the gears: 5200 to 8050 rpm in six seconds, so the shift and the limiter come by
        rpm = 5200 + 2850 * ((now - self.t0) % 6.0) / 6.0
        press = 70.0 if 200 <= cycle < 206 or 440 <= cycle < 446 else min(480.0, 60 + 0.07 * rpm)
        return {'status': {'connected': True, 'logging': {'active': True},
                           'video': {'recording': True, 'minutes_left': max(0, 150 - (now - self.t0) / 60)},
                           'podium': {'enabled': True, 'state': 'streaming', 'last_sent_age_ms': 120}},
                'sample': {'values': {'Lat': lat, 'Lon': lon, 'GPSSpeed': 80.0 + 0.012 * (rpm - 5200), 'RPM': rpm},
                           'can_signals': {'OilTemp': oil, 'WaterTemp': oil - 10, 'OilPress': press},
                           'gnss_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'lap': lap}}


def fixed_state(config, name, rpm=None):
    """One screen for checking the layout (the gap is filled in by hand: it needs a best lap's track).
    rpm: the engine speed instead of the state's own (to see the bar at a given point)."""
    lap = {'CurrentLap': 23, 'LapCount': 22, 'ElapsedTime': 72.3 / 60, 'LapTime': 112.34 / 60, 'BestLap': 111.12 / 60,
           'RaceTime': 2175 / 60, 'LapDiffS': 0.41, 'LastLapPit': False,
           'Sector': 3, 'LastSector': 2, 'SectorTime': 31.42 / 60, 'SectorDiffS': -0.31}
    # oil C, water C, oil pressure kPa (at 5200 rpm; idling in the box): warn is the oil alone,
    # warnpress the pressure alone, warn2 pressure and oil, warn3 all three
    temps = {'normal': (98, 88, 420), 'start': (92, 84, 430), 'pit': (101, 91, 410), 'pitbox': (101, 91, 150),
             'warn': (122, 104, 400), 'warnpress': (104, 94, 85), 'warn2': (124, 105, 150), 'warn3': (128, 113, 140),
             'lost': (None, 93, 420), 'stale': (98, 88, 420), 'pitlane': (101, 91, 300),
             'shift': (98, 88, 450), 'limit': (98, 88, 460), 'slower': (98, 88, 420), 'sendwait': (98, 88, 420), 'sendoff': (98, 88, 420)}[name]
    if name == 'start':
        lap.update(CurrentLap=0, LapCount=0, ElapsedTime=None, LapTime=None, BestLap=None, RaceTime=None, LapDiffS=None, LastLapPit=None)
    if name in ('pit', 'pitbox', 'pitlane'):  # the in lap was a pit lap, the running lap started in the pit lane
        lap.update(ElapsedTime=21.4 / 60, LapTime=221.07 / 60, LapDiffS=None, LastLapPit=True, LapStartPit=True)
    # before the start the video light is yellow: 108 minutes left is short of the race
    # sending: rows going out, but for sendwait (the link lost, trying again) and sendoff (switched off)
    podium = {'sendwait': {'enabled': True, 'state': 'retry', 'last_sent_age_ms': 14200},
              'sendoff': {'enabled': False, 'state': 'off', 'last_sent_age_ms': None}}.get(
                  name, {'enabled': True, 'state': 'streaming', 'last_sent_age_ms': 120})
    frame = {'status': {'connected': True, 'logging': {'active': True},
                        'video': {'recording': True, 'minutes_left': 108 if name == 'start' else 150},
                        'podium': podium},
             'sample': {'values': {'Lat': 38.1423, 'Lon': 140.777,
                                   'GPSSpeed': {'pitbox': 0.0, 'pitlane': 63.0, 'shift': 131.0, 'limit': 133.0}.get(name, 120.0),
                                   'RPM': rpm if rpm is not None else
                                   {'pitbox': 900.0, 'pitlane': 3900.0, 'shift': 7760.0, 'limit': 8010.0}.get(name, 6400.0)},
                        'can_signals': {'OilTemp': temps[0], 'WaterTemp': temps[1], 'OilPress': temps[2]},
                        'gnss_utc': '2026-11-08T02:16:15Z', 'lap': lap}}
    model = DashModel(config)
    for k in range(80):  # past the warning hold time
        state, _ = model.update(frame, 100.0 + k * 0.1)
    if name == 'stale':
        state, _ = model.update(None, 100.0 + 8 + 12)
    if name == 'slower':
        state.update(delta='+1.27', delta_kind='slower', delta_frac=0.635)
    elif name not in ('start', 'stale', 'pit', 'pitbox', 'pitlane'):
        state.update(delta='−0.84', delta_kind='faster', delta_frac=-0.42)
    return state


def rgb(colour):
    return tuple(int(colour[k:k + 2], 16) / 255.0 for k in (1, 3, 5))


class Painter:
    """Text for paint(): the number font and the text font picked from what the machine has, sizes in the
    design's pixels (the cairo context is scaled to the screen), positions by the baseline as in the mock-up."""

    def __init__(self, Pango, PangoCairo):
        self.Pango, self.PangoCairo = Pango, PangoCairo
        have = {family.get_name() for family in PangoCairo.FontMap.get_default().list_families()}
        self.num_font = next((font for font in NUM_FONTS if font[0] in have), NUM_FONTS[-1])
        self.text_font = next((font for font in TEXT_FONTS if font[0] in have), TEXT_FONTS[-1])
        self.weights = {300: Pango.Weight.LIGHT, 400: Pango.Weight.NORMAL, 500: Pango.Weight.MEDIUM,
                        600: Pango.Weight.SEMIBOLD, 700: Pango.Weight.BOLD}
        self.fonts = {}
        self.tabular = Pango.AttrList()
        self.tabular.insert(Pango.attr_font_features_new('tnum=1'))

    def font(self, px, jp, light):
        key = (round(px, 1), jp, light)
        if key not in self.fonts:
            if jp:
                (family, weight), variations = self.text_font, None
            else:
                family, weight, variations, thin = self.num_font
                if light:
                    weight, variations = (300, thin) if thin else (400, None)
            desc = self.Pango.FontDescription()
            desc.set_family(f'{family}, {TEXT_FONTS[0][0]}, sans-serif')
            desc.set_weight(self.weights[weight])
            desc.set_absolute_size(px * self.Pango.SCALE)
            if variations:
                desc.set_variations(variations)
            self.fonts[key] = desc
        return self.fonts[key]

    def layout(self, ctx, text, px, jp=False, light=False):
        layout = self.PangoCairo.create_layout(ctx)
        layout.set_font_description(self.font(px, jp, light))
        if not jp:  # digits all one width (a font whose own digits differ), so a running time does not shake
            layout.set_attributes(self.tabular)
        layout.set_text(text, -1)
        return layout

    def width(self, ctx, text, px, jp=False, light=False):
        return self.layout(ctx, text, px, jp, light).get_size()[0] / self.Pango.SCALE

    def text(self, ctx, x, y, px, text, colour, anchor='start', jp=False, light=False, fit=None):
        """Draws text with its baseline at y and its start / middle / end at x; fit: no wider than this
        (the size comes down, for a font wider than the one the layout was drawn with). Returns the width."""
        layout = self.layout(ctx, text, px, jp, light)
        width = layout.get_size()[0] / self.Pango.SCALE
        if fit and width > fit:
            layout = self.layout(ctx, text, px * fit / width, jp, light)
            width = layout.get_size()[0] / self.Pango.SCALE
        ctx.set_source_rgb(*rgb(colour))
        ctx.move_to(x - {'start': 0.0, 'middle': width / 2, 'end': width}[anchor],
                    y - layout.get_baseline() / self.Pango.SCALE)
        self.PangoCairo.show_layout(ctx, layout)
        return width

    def num(self, ctx, x, y, px, text, colour, anchor='start', fit=None):
        """A value; one that has not come ('--') as two thin grey dashes, smaller, so it does not shout."""
        if text == '--':
            return self.text(ctx, x, y - px * 0.08, px * 0.6, '– –', DIM, anchor, light=True)
        return self.text(ctx, x, y, px, text, colour, anchor, fit=fit)


def paint(ctx, p, s, W, seg_colours, now):
    """The whole screen from one state of dash_model, on a canvas W wide and DESIGN_H tall (1280 x 800 is
    the mock-up docs/design/dash_mock_simple_20261119.html; a wider screen spreads sideways). No frames, no
    caption plates; colour only where it says something: the engine speed bar, the gap, the warnings."""
    flash = now % FLASH_PERIOD_S >= FLASH_PERIOD_S / 2
    left, right, cx = 24.0, W - 24.0, W / 2.0

    def rect(x, y, w, h, colour, radius=0.0):
        ctx.set_source_rgb(*rgb(colour))
        if radius:
            ctx.new_sub_path()
            for ax, ay, start in ((x + w - radius, y + radius, -0.5), (x + w - radius, y + h - radius, 0.0),
                                  (x + radius, y + h - radius, 0.5), (x + radius, y + radius, 1.0)):
                ctx.arc(ax, ay, radius, start * math.pi, (start + 0.5) * math.pi)
            ctx.close_path()
        else:
            ctx.rectangle(x, y, w, h)
        ctx.fill()

    # The top: the engine speed bar (segments as an AiM's shift lights), and at its right end the engine
    # speed over the speed, the same size, level with the bar's middle (the user's call, 2026-11-19: the
    # bar is what is read, so the numbers give it their room)
    num_right = right - 60
    num_w = max(96.0, p.width(ctx, '8888', 48))
    bar_x0, bar_x1 = 12.0, num_right - num_w - 26
    pitch = (bar_x1 - bar_x0) / (len(seg_colours) - 1 + SEG_FILL)
    lit, mode = s.get('rpm_lit', 0), s.get('rpm_mode')
    for k, colour in enumerate(seg_colours):
        # lit up to the shift point, then the whole bar red, flashing twice a second
        shade = (SEG_DARK if flash else RED) if mode else SEG[colour] if k < lit else OFF
        rect(bar_x0 + k * pitch, 24, pitch * SEG_FILL, 88, shade, 4)
    plate_x = num_right - num_w - 8
    limit = mode == 'limit'
    if limit:  # at the limiter the engine speed turns black on white
        rect(plate_x, 21, right - plate_x, 46, WHITE)
    p.num(ctx, num_right, 61, 48, s.get('rpm', '--'), '#000000' if limit else WHITE, 'end', fit=num_w)
    p.text(ctx, num_right + 7, 61, 22, 'rpm', '#000000' if limit else UNIT)
    speed_kind = s.get('speed_kind')
    if speed_kind == 'over':  # over the pit lane's limit: a red plate
        rect(plate_x, 70, right - plate_x, 46, PLATE_RED)
    p.num(ctx, num_right, 110, 48, s.get('speed', '--'), '#ffd060' if speed_kind == 'warn' else WHITE, 'end', fit=num_w)
    p.text(ctx, num_right + 7, 110, 22, 'km/h', WHITE if speed_kind == 'over' else UNIT)

    # The gap to the best lap: the one big thing. On a pit lap its place says PIT IN / PIT OUT in blue
    # (a normal pit stop is information, not a warning), and the sector just completed stands small beside it
    p.text(ctx, cx, 160, 24, 'ベスト比', GREY, 'middle', jp=True)
    notice, notice_kind = s.get('notice', ''), s.get('notice_kind')
    if notice and notice_kind == 'pit':
        p.text(ctx, cx, 364, 180, notice, BLUE, 'middle', fit=W - 2 * 120)
    else:
        colour = {'faster': GREEN, 'slower': RED}.get(s.get('delta_kind'), WHITE)
        p.num(ctx, cx, 372, 230, s['delta'] if s.get('delta_kind') else '--', colour, 'middle', fit=W - 2 * 300)
        if notice:
            p.text(ctx, W - 120, 372, 34, notice, {'faster': GREEN, 'slower': RED}.get(notice_kind, WHITE), 'end')
    # its ruler: nought in the middle, faster to the left, slower to the right (delta_full_scale_s at the ends)
    half, tape_y = cx - 120, 412.0
    rect(cx - half, tape_y, 2 * half, 1, '#444444')
    for k in range(-4, 5):
        tick = 16 if k % 2 == 0 else 9
        rect(cx + k * half / 4 - 0.5, tape_y - tick / 2, 1, tick, DIM)
    frac = s.get('delta_frac')
    if frac is not None and abs(frac) >= 1e-3 and notice_kind != 'pit':
        width = max(2.0, half * abs(frac))
        rect(cx - width if frac < 0 else cx, tape_y - 7, width, 14, GREEN if frac < 0 else RED)
    rect(cx - 1.5, tape_y - 16, 3, 32, WHITE)

    # The lap times: the last lap, the running lap, the best. A warning takes this row as a red band, each
    # warning that is on side by side with its value big (oil pressure first); the gap above and the
    # row below stay readable (never the whole screen: the pit must see the rest)
    warns = s['warns'][:len(WARN_SCALE)]
    if warns:
        # flashing just after a warning comes on: dark red half the time, the white text stays
        rect(left, 446, right - left, 146, '#520808' if s.get('warn_flash') and flash else PLATE_RED)
        scale, cell = WARN_SCALE[len(warns)], (right - left) / len(warns)
        for k, warn in enumerate(warns):
            name_px, value_px, unit_px, gap = 62 * scale, 124 * scale, 54 * scale, 28 * scale
            widths = (p.width(ctx, warn['label'], name_px, jp=True), p.width(ctx, warn['value'], value_px),
                      p.width(ctx, warn['unit'], unit_px))
            x = left + cell * (k + 0.5) - (sum(widths) + 1.4 * gap) / 2
            base = 519 + 0.36 * value_px  # the number's middle on the band's middle
            p.text(ctx, x, base - 0.14 * value_px, name_px, warn['label'], '#ffffff', jp=True)
            p.text(ctx, x + widths[0] + gap, base, value_px, warn['value'], '#ffffff')
            p.text(ctx, x + widths[0] + gap + widths[1] + 0.4 * gap, base, unit_px, warn['unit'], '#ffffff')
    else:
        column = (right - left) / 3 - 20
        cap_w = p.text(ctx, left, 476, 24, '前周', GREY, jp=True)
        if s.get('last_note'):
            p.text(ctx, left + cap_w + 16, 476, 28, s['last_note'],
                   {'pit': BLUE, 'slower': RED, 'faster': GREEN}.get(s.get('last_note_kind'), WHITE))
        p.num(ctx, left, 574, 100, s['last'], WHITE, fit=column)
        p.text(ctx, cx, 476, 24, '今の周', GREY, 'middle', jp=True)
        p.num(ctx, cx, 574, 100, s['lap_now'], WHITE, 'middle', fit=column)
        p.text(ctx, right, 476, 24, 'ベスト', GREY, 'end', jp=True)
        p.num(ctx, right, 574, 100, s['best'], WHITE, 'end', fit=column)

    # The lap number, the time since the start, the clock: the same three places, a size smaller
    rect(0, 608, W, 1, OFF)
    p.text(ctx, left, 650, 24, '周', GREY, jp=True)
    p.num(ctx, left, 724, 68, s['lap_no'], WHITE)
    p.text(ctx, cx, 650, 24, '経過', GREY, 'middle', jp=True)
    if s['elapsed'] == 'スタート待ち':
        p.text(ctx, cx, 716, 44, s['elapsed'], WHITE, 'middle', jp=True)
    else:
        p.num(ctx, cx, 724, 68, s['elapsed'], WHITE, 'middle')
    p.text(ctx, right, 650, 24, '時刻', GREY, 'end', jp=True)
    p.num(ctx, right, 724, 68, s['clock'], WHITE, 'end')

    if s['stale']:  # no values: say so over everything but the lights below
        rect(0, 0, W, 742, '#1a1a1a')
        waited = s.get('stale_s')
        p.text(ctx, cx, 370, 44, 'ロガーの値を待っています' if waited is None else 'ロガーの値が来ていません',
               '#d8d8d8', 'middle', jp=True)
        if waited is not None:
            p.text(ctx, cx, 430, 24, f'最後に受け取ってから {int(waited)} 秒', '#d8d8d8', 'middle', jp=True)

    # The logger's lights, small along the bottom: all well is a green dot and grey words; what needs a
    # look is a yellow plate, what has stopped a red one. From the left: the log, the burnt-in video
    # (with the time it can still record), sending (SPEC.md M-2), GNSS, the oil sensors. A new light is
    # one more entry here: the row has the room
    lights = [('記録', 'ok') if s['rec'] else ('記録停止', 'bad')]
    if s.get('video'):
        lights.append((s['video'], 'ok' if s.get('video_kind') == 'ok' else 'warn'))
    # sending (dash_model.send_light): yellow when it is on but nothing goes out, grey when switched off
    # or not known (not a fault: nothing to do while driving)
    lights.append((s.get('send', '送信 --'), {'ok': 'ok', 'warn': 'warn'}.get(s.get('send_kind'), 'off')))
    lights.append(('GNSS', 'ok') if s['gnss'] else ('GNSS未測位', 'warn'))
    lights.append((s['sensor'][0], 'ok' if s['sensor'][1] else 'warn'))
    x = right
    for words, kind in reversed(lights):
        width = p.width(ctx, words, 22, jp=True)
        if kind in ('warn', 'bad'):
            rect(x - width - 24, 757, width + 24, 33, '#ffb020' if kind == 'warn' else '#d81e1e')
            p.text(ctx, x - 12, 782, 22, words, '#1c1000' if kind == 'warn' else '#ffffff', 'end', jp=True)
            x -= width + 24 + 30
        else:
            p.text(ctx, x, 782, 22, words, GREY, 'end', jp=True)
            rect(x - width - 20, 766, 10, 10, GREEN if kind == 'ok' else DIM)
            x -= width + 20 + 32


def snapshot(args, config):
    """Paints one screen straight into a PNG (--snapshot): the fixed screen of --state, else what the
    logger is sending now. No window and no X needed. The size is --size, else the screen's, else the design's."""
    import cairo
    import gi
    gi.require_version('Pango', '1.0')
    gi.require_version('PangoCairo', '1.0')
    from gi.repository import Pango, PangoCairo
    if args.size:
        w, h = (int(v) for v in args.size.lower().split('x'))
    else:
        try:
            gi.require_version('Gdk', '3.0')
            from gi.repository import Gdk
            screen = Gdk.Screen.get_default()
            w, h = screen.get_width(), screen.get_height()
        except Exception:
            w, h = int(DESIGN_W), int(DESIGN_H)
    if args.state:
        state = fixed_state(config, args.state, args.rpm)
    else:
        state, _ = DashModel(config, LAPREF_PATH).update(fetch(config['api']), time.monotonic())
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
    ctx = cairo.Context(surface)
    k = min(h / DESIGN_H, w / DESIGN_W)
    ctx.translate(0, (h - DESIGN_H * k) / 2)
    ctx.scale(k, k)
    # --flash-dark: the dark half of the flashing (the bar at the shift point, a new warning's band)
    paint(ctx, Painter(Pango, PangoCairo), state, w / k, segment_colours(rpm_segments(config)),
          FLASH_PERIOD_S * 0.75 if args.flash_dark else 0.0)
    surface.write_to_png(args.snapshot)


def run_gui(args, config):
    import warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning)  # Gdk.Screen.get_width / get_height
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    gi.require_version('Pango', '1.0')
    gi.require_version('PangoCairo', '1.0')
    from gi.repository import Gdk, GLib, Gtk, Pango, PangoCairo

    class Dash(Gtk.Window):
        """One drawing area painted by paint() (2026-11-19; it was boxes and labels styled with CSS):
        the layout is fixed by the mock-up's coordinates, which GTK's boxes could not hold to."""

        def __init__(self):
            super().__init__(title='EcoCapture DASH')
            self.set_decorated(False)
            screen = self.get_screen()
            if args.size:
                self.size = tuple(int(v) for v in args.size.lower().split('x'))
            else:  # one X screen, one output: the screen is what to cover (deprecated in GTK 3.22, still there)
                self.size = (screen.get_width(), screen.get_height())
            self.set_default_size(*self.size)
            self.move(0, 0)
            self.state = None
            self.painter = Painter(Pango, PangoCairo)
            self.seg_colours = segment_colours(rpm_segments(config))
            self.area = Gtk.DrawingArea()
            self.area.connect('draw', self.on_draw)
            self.add(self.area)
            self.connect('realize', self.on_realize)
            self.connect('configure-event', self.on_configure)
            screen.connect('size-changed', self.on_screen)  # the HDMI mode set again after a reconnect
            self.connect('destroy', lambda _w: Gtk.main_quit())

        def on_draw(self, _widget, ctx):
            w, h = self.area.get_allocated_width(), self.area.get_allocated_height()
            ctx.set_source_rgb(0, 0, 0)
            ctx.paint()
            if self.state:
                # the design's height fills the screen and the width spreads; a screen narrower than
                # the design (4:3) is fitted by its width instead, with black above and below
                k = min(h / DESIGN_H, w / DESIGN_W)
                ctx.translate(0, (h - DESIGN_H * k) / 2)
                ctx.scale(k, k)
                paint(ctx, self.painter, self.state, w / k, self.seg_colours, time.monotonic())
            return False

        def on_configure(self, _widget, event):
            if (event.width, event.height) != self.size and not args.size:
                self.size = (event.width, event.height)
            return False

        def on_screen(self, screen):
            if not args.size:
                self.size = (screen.get_width(), screen.get_height())
                self.resize(*self.size)

        def on_realize(self, _widget):
            window = self.get_window()
            if not args.size:
                window.set_override_redirect(True)  # no window manager on :2; cover the whole screen
            window.set_cursor(Gdk.Cursor.new_for_display(window.get_display(), Gdk.CursorType.BLANK_CURSOR))

        def keep_above(self):
            window = self.get_window()
            if window:
                window.raise_()
            return True

        def show_state(self, s):
            self.state = s
            self.area.queue_draw()  # every tick: the flashing (the bar, the band) runs on the clock

    dash = Dash()
    dash.show_all()
    sound = None if args.state else Sound(config)  # a layout check never makes a sound
    lock = threading.Lock()
    latest = {}

    if args.state:
        latest['state'] = fixed_state(config, args.state, args.rpm)
    else:
        model = DashModel(config, None if args.demo else LAPREF_PATH)
        demo = DemoFeed(time.monotonic()) if args.demo else None

        def poll():
            while True:
                started = time.monotonic()
                frame = demo.frame(started) if demo else fetch(config['api'])
                state, kind = model.update(frame, time.monotonic())
                if kind and sound:
                    sound.play(kind)
                with lock:
                    latest['state'] = state
                time.sleep(max(.02, .1 - (time.monotonic() - started)))
        threading.Thread(target=poll, daemon=True).start()

    def tick():
        with lock:
            state = latest.get('state')
        if state:
            dash.show_state(state)
        return True

    if not args.no_pause:  # the covered admin window, as touch_launcher.py does
        try:
            from display_load_control import set_paused
            set_paused('ecocapture-native', True)
            atexit.register(set_paused, 'ecocapture-native', False)
        except Exception:
            pass

    def stop(*_args):
        GLib.idle_add(Gtk.main_quit)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    GLib.timeout_add(100, tick)  # the values come at most 10 times a second
    GLib.timeout_add(1000, dash.keep_above)
    Gtk.main()


def main(argv=None):
    parser = argparse.ArgumentParser(description='EcoCapture DASH')
    parser.add_argument('--config', default=str(CONFIG_PATH))
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--state', choices=['normal', 'slower', 'start', 'pit', 'pitbox', 'pitlane', 'shift', 'limit', 'warn',
                                            'warnpress', 'warn2', 'warn3', 'lost', 'stale', 'sendwait', 'sendoff'])
    parser.add_argument('--sound', choices=['warn'])
    parser.add_argument('--rpm', type=float, help='with --state: this engine speed instead of the state\'s own')
    parser.add_argument('--size')
    parser.add_argument('--snapshot')
    parser.add_argument('--no-pause', action='store_true')
    parser.add_argument('--flash-dark', action='store_true', help='with --snapshot: the dark half of the flashing')
    parser.add_argument('--volume', type=float, help='with --sound: 0 (silent, checks the path) to 1')
    args = parser.parse_args(argv)
    config = load_config(args.config)
    if args.sound:
        sound = {**config['sound'], 'enabled': True}
        if args.volume is not None:
            sound['volume'] = args.volume
        proc = Sound({**config, 'sound': sound}).play(args.sound)
        return 0 if proc is not None and proc.wait() == 0 else 1
    if args.snapshot:
        snapshot(args, config)
    else:
        run_gui(args, config)
    return 0


if __name__ == '__main__':
    sys.exit(main())
