# Open-source / general-purpose tools for analysing self-built logger data (as of 2026-11-14)

Scope: tools we could hand to team members as-is, or reuse/embed in our own PC app (Python backend + browser UI). Benchmark: MoTeC i2 Pro (lap overlay by distance, time slip, track map, math channels, video). Repo metadata (licence SPDX id, stars, last push, latest release) was read from the GitHub API on 2026-11-14 via `gh api repos/<owner>/<repo>` and `.../releases/latest`; those are cited as the repo URL.

## Q1. Licence (exact) and implications for bundling/embedding in a public repo / possible commercial product

### Takeaway
Permissive (MIT / BSD / Apache-2.0) options exist for every layer we would embed: TrackDataAnalysis (MIT), FastF1 (MIT), uPlot (MIT), Plotly.js (MIT), ECharts (Apache-2.0), Leaflet (BSD-2), cantools (MIT), SavvyCAN (MIT). The copyleft items to keep at arm's length (ship separately / don't link into our code) are: RaceCapture App (GPL-3.0), ldparser (GPL-3.0), Grafana (AGPL-3.0), asammdf (LGPL-3.0), python-can (LGPL-3.0), PlotJuggler (MPL-2.0, file-level copyleft only), and libmpv (GPL-2.0+ by default, LGPL-2.1+ only if built that way), which TrackDataAnalysis' Windows installer bundles.

### Cited Findings
- racer-coder/TrackDataAnalysis: licence **MIT**, 66 stars, last push 2026-09-19, not archived; description "GUI for analyzing AiM, MoTeC, or RaceCapture data logs". Source files carry "Copyright 2024, Scott Smith. MIT License" — [GitHub repo](https://github.com/racer-coder/TrackDataAnalysis); [data/autosport_labs.py](https://github.com/racer-coder/TrackDataAnalysis/blob/main/data/autosport_labs.py)
- TrackDataAnalysis depends on PySide6 (Qt for Python; LGPL-3.0 per Qt's standard licensing, not checked here), numpy, Cython, dacite, glfw, pyyaml; packaged with cx_freeze on Windows — [requirements.txt](https://github.com/racer-coder/TrackDataAnalysis/blob/main/requirements.txt)
- TrackDataAnalysis' Windows build copies `ui/libmpv-2.dll` into the installer (`include_files`) — [setup.py](https://github.com/racer-coder/TrackDataAnalysis/blob/main/setup.py). Its vendored `ui/mpv.py` says: "python-mpv inherits the underlying libmpv's license, which can be either GPLv2 or later (default) or LGPLv2.1 or later" — [ui/mpv.py](https://github.com/racer-coder/TrackDataAnalysis/blob/main/ui/mpv.py). The mpv repo licence shows as NOASSERTION (mixed GPL/LGPL) in the API — [mpv-player/mpv](https://github.com/mpv-player/mpv)
- PlotJuggler: licence **MPL-2.0**, 6,316 stars, last push 2026-11-13, latest release 4.1.0 (2026-11-05) — [GitHub repo](https://github.com/PlotJuggler/PlotJuggler); the README says it is "Released under the Mozilla Public License 2.0" — [README](https://github.com/facontidavide/PlotJuggler)
- asammdf: GitHub shows NOASSERTION, but the LICENSE file is **GNU LGPL v3** ("Copyright 2017–2023 Daniel Hrisca"); 821 stars; latest release 8.8.33 (2026-11-11) — [LICENSE](https://github.com/danielhrisca/asammdf/blob/master/LICENSE)
- RaceCapture App (Autosport Labs, Python/Kivy): a Gitee mirror shows **GPL-3.0** with the full GPLv3 text, README "Next Gen version of the RaceCapture App", 1,758 commits — [Gitee mirror](https://gitee.com/mirrors_Knio/RaceCapture_App). The official repo `github.com/autosportlabs/RaceCapture_App` returned **HTTP 404** from the GitHub API on 2026-11-14 (it may be private, renamed or deleted; not confirmed) — `gh api repos/autosportlabs/RaceCapture_App`. Autosport Labs' firmware is GPL-3.0 and **archived** (last push 2022-08-28) — [RaceCapture-Pro_firmware](https://github.com/autosportlabs/RaceCapture-Pro_firmware). Autosport Labs also has an old GPL-3.0 "RaceAnalyzer" (last push 2014) — [RaceAnalyzer](https://github.com/autosportlabs/RaceAnalyzer)
- FastF1: **MIT**, 5,561 stars, release v3.9.2 (2026-11-02) — [theOehrly/Fast-F1](https://github.com/theOehrly/Fast-F1)
- uPlot: **MIT**, 10,637 stars, last push 2026-11-14, latest tagged release 1.6.32 (2025-03-14) — [leeoniya/uPlot](https://github.com/leeoniya/uPlot)
- Apache ECharts: **Apache-2.0**, 67,720 stars, release 6.1.0 (2026-05-19) — [apache/echarts](https://github.com/apache/echarts)
- Plotly.js: **MIT**, 18,382 stars, release v4.3.0 (2026-11-10) — [plotly/plotly.js](https://github.com/plotly/plotly.js)
- Grafana: **AGPL-3.0**, 77,894 stars, release v13.3.1 (2026-11-10) — [grafana/grafana](https://github.com/grafana/grafana)
- Leaflet: **BSD-2-Clause**, 45,924 stars — [Leaflet/Leaflet](https://github.com/Leaflet/Leaflet). MapLibre GL JS: API shows NOASSERTION (its LICENSE is BSD-3-style per my prior knowledge; **unverified here**) — [maplibre-gl-js](https://github.com/maplibre/maplibre-gl-js)
- CAN-side helpers: cantools **MIT** (2,315 stars) — [cantools](https://github.com/cantools/cantools); python-can **LGPL-3.0** — [python-can](https://github.com/hardbyte/python-can); SavvyCAN **MIT** (Qt GUI, last push 2026-11-04) — [SavvyCAN](https://github.com/collin80/SavvyCAN)
- MoTeC .ld file parser `gotzl/ldparser`: **GPL-3.0**, 83 stars, last push 2026-02-22 — [ldparser](https://github.com/gotzl/ldparser). Aim_2_MoTeC converter: MIT — [Aim_2_MoTeC](https://github.com/ludovicb1239/Aim_2_MoTeC)
- MegaLogViewer HD: proprietary, "Heavy Duty - Premium Edition of MegaLogViewer", free trial + paid registration; the page does not show a price — [EFI Analytics](https://www.efianalytics.com/MegaLogViewerHD/)

### Inferences
- MIT/BSD/Apache code (TrackDataAnalysis, FastF1 snippets, uPlot, Plotly.js, ECharts, Leaflet, cantools) can be copied into our public repo and a future commercial product, provided we keep the copyright notice / LICENSE text (Apache-2.0 also wants the NOTICE file kept and changes marked).
- Reusing TrackDataAnalysis' *algorithms* (GPS lap insert, distance calculation, time slip, the math-expression evaluator) in our own Python is the cleanest licence-wise. Redistributing its **Windows MSI** means shipping libmpv-2.dll. Whether that DLL is a GPL or LGPL build is not stated in the repo (unverified). If it is GPL, anyone redistributing the installer has to meet GPL source-offer terms for mpv. Linking only to the user's own installed TDA (not redistributing) avoids this.
- GPL-3.0 RaceCapture App code must not be pasted into our app unless the whole app goes GPL-3.0. Users can install it as a separate program.
- Grafana (AGPL) is fine to run unmodified as a separate service (we already run it on the home server). Embedding or modifying it in a product we offer over a network would bring AGPL source obligations.
- PlotJuggler (MPL-2.0) can be handed to users as-is. Modifying its files means publishing those modified files under MPL; it can sit alongside proprietary code.
- asammdf / python-can (LGPL-3.0) are fine as unmodified pip dependencies called from our Python. In a frozen commercial build, users must be able to replace the library (LGPL relinking clause). Easy with plain Python packages; somewhat harder with PyInstaller one-file builds.

### Gaps
- Exact licence of the libmpv-2.dll build used in TrackDataAnalysis releases (GPL vs LGPL). It was not checked; it depends on the SourceForge build the author used.
- Whether the official RaceCapture_App GitHub repo still exists publicly (404 on 2026-11-14). The latest commit date on the Gitee mirror was not shown.
- MegaLogViewer HD current price: the EFI Analytics product page shows no price, and the guessed registration URL returned 404.

## Q2. Input formats, and what we would need to export

### Takeaway
TrackDataAnalysis has **no generic CSV importer**, but it natively reads the **Autosport Labs (RaceCapture) .log format**, which is a simple CSV. Our logger already speaks RCP, so writing our post-session CSV in RaceCapture .log layout is the lowest-effort way to open our data in TDA (and in RaceCapture's own app). PlotJuggler and MegaLogViewer read arbitrary CSV. asammdf needs MDF4 (could be useful for raw CAN, not for lap analysis).

### Cited Findings
- TrackDataAnalysis opens "AiM XRK, MoTeC LD, ECUMaster ADULOG and EMUPROLOG, Autosport Lab LOG, RaceLogic VBOX, Race Technology RUN, MegaLogViewer MLG, and iRacing IBT files natively" — [README](https://github.com/racer-coder/TrackDataAnalysis). The `data/` folder also contains `gpmf.py` (GoPro metadata) — [data/](https://github.com/racer-coder/TrackDataAnalysis/tree/main/data). The README's feature table lists "Many data formats: CSV (Pro)" only for MoTeC; TDA itself has no CSV loader in `data/` — [README](https://github.com/racer-coder/TrackDataAnalysis)
- TDA's Autosport Labs loader: comma-separated file; header cells are pipe-delimited `"Name"|"units"|...`; the first column is the interval timecode (ms, handled separately); a **`LapCount`** channel is required to split laps; the `Utc` value is parsed for log date/time; key channels are mapped as **`Speed`, `Latitude`, `Longitude`, `Altitude`**; empty cells are skipped, so mixed-rate channels are fine — [data/autosport_labs.py](https://github.com/racer-coder/TrackDataAnalysis/blob/main/data/autosport_labs.py)
- TDA can also insert laps automatically from GPS (`try_gps_lap_insert` using lat/lon to ECEF), originally for AiM files — [data/distance.py](https://github.com/racer-coder/TrackDataAnalysis/blob/main/data/distance.py); changelog 0.3.1 "Automatic GPS lap insert for AiM files" — [README](https://github.com/racer-coder/TrackDataAnalysis)
- PlotJuggler reads "CSV, MCAP, Parquet, PX4 ULog, LeRobot, MP4, PCD and PLY" — [README](https://github.com/facontidavide/PlotJuggler)
- MegaLogViewer HD loads "nearly any CSV or delimited file" plus binary logs from Motec, MegaSquirt, HP Tuners, Haltech, Torque and others — [EFI Analytics](https://www.efianalytics.com/MegaLogViewerHD/)
- asammdf is a "Fast Python reader and editor for ASAM MDF / MF4" — [asammdf](https://github.com/danielhrisca/asammdf)
- RCP2GEMS converts Autosport Labs logs ("a form of CSV") to a CSV format GEMS reads — [TDA README](https://github.com/racer-coder/TrackDataAnalysis); [RCP2GEMS](https://github.com/autosportlabs/RCP2GEMS)

### Inferences
- Recommended export for "hand to users": a `.log` file in RaceCapture layout (Interval[ms], Utc, LapCount, Latitude, Longitude, Speed, RPM, TPS, temps …, with units in the header). It opens in TDA directly, and probably also in the RaceCapture App's analysis view (not tested).
- If sector times should show in TDA, sectors are defined in TDA's own track editor (main branch), not imported from our file. See Q3.
- Writing MoTeC .ld would open the door to i2 (excluded) and TDA. The only well-known parser (ldparser) is GPL-3.0, so writing .ld ourselves would need a clean implementation. Not worth it given the .log route.
- For raw CAN, MDF4 via asammdf (LGPL) or plain candump/CSV in SavvyCAN (MIT) are options. Neither is a lap-analysis tool.

### Gaps
- Not tested: whether a .log produced by our logger opens without errors in the current TDA build (needs a trial file). Also unknown how TDA handles `Speed` units (its changelog says units support fixes distance "when speed is not m/s").
- The RaceCapture App's import formats for analysis were not confirmed from primary docs (the wiki URL tried returned 404).

## Q3. Features vs MoTeC i2 Pro (lap overlay by distance, time slip, track map/GPS line, sectors, math channels, video sync)

### Takeaway
TrackDataAnalysis is the only open-source desktop tool found that covers nearly all of the i2 Pro benchmark: distance/time overlay, time slip, GPS map with line comparison, math channels and synced video, plus (on unreleased main) sector table, track editor, histogram, scatter and lift-and-coast. PlotJuggler is a strong general time-series viewer but has no lap/distance concepts. The RaceCapture App offers basic lap comparison. MegaLogViewer HD is ECU-tuning oriented (file compare, calculated fields), with no documented lap/track/video features.

### Cited Findings
- TDA (v0.4.1 README): "Time/distance graph with overlaying channels … multiple laps with individual lap offsets, and time slip"; "GPS map with optional satellite background for line comparison"; "Video from almost anything can be included. Playback is kept synchronized even in distance mode by speeding up/slowing down playback of the alternate lap"; "Math channels"; session metadata database — [README](https://github.com/racer-coder/TrackDataAnalysis)
- TDA README "Future (aka missing) features": track editor for sections, channel graphs (bar, histogram…), reports (min/max/avg, sector comparison) — [README](https://github.com/racer-coder/TrackDataAnalysis). The **main branch** now has `ui/sector_table.py` ("Sector comparison table: shows time per sector per lap with delta coloring", sectors defined via "Tools > Track editor"), `ui/track.py`, `ui/histogram.py`, `ui/scatter.py`, `ui/liftcoast.py` — [ui/](https://github.com/racer-coder/TrackDataAnalysis/tree/main/ui); recent commits include "ui/liftcoast: Attempted lift & coast cost/benefit calculator" (2026-07-05) and "ui/histogram: Optionally show cumulative percentage" (2026-06-06) — [commits](https://github.com/racer-coder/TrackDataAnalysis/commits/main)
- TDA video: one video file per log; alignment is manual ("enable 'Set video alignment' … drag the bottom slider until the video lines up") — [README](https://github.com/racer-coder/TrackDataAnalysis). Video playback uses libmpv — [ui/video.py](https://github.com/racer-coder/TrackDataAnalysis/blob/main/ui/video.py)
- TDA satellite maps need a (free) MapTiler API key; otherwise the map shows the GPS line without background — [README](https://github.com/racer-coder/TrackDataAnalysis)
- TDA math: "0.4.0 Initial math expression support" — [README](https://github.com/racer-coder/TrackDataAnalysis); parser in [data/math_eval.py](https://github.com/racer-coder/TrackDataAnalysis/blob/main/data/math_eval.py) using the bundled `sly` lexer/parser
- TDA author's own comparison: MoTeC i2 video is "Pro (but didn't work for me)"; RaceCapture is marked YES for video and cross-platform but "no" for many data formats — [README](https://github.com/racer-coder/TrackDataAnalysis)
- PlotJuggler: drag signals into time-series and XY plots; derived series via custom transforms in Lua and Python; FFT/integration/rate-of-change; MP4 and H.264/H.265/AV1 video support; no lap- or distance-based features mentioned — [README](https://github.com/facontidavide/PlotJuggler). 4.1.0 adds GPU rendering via Qt RHI (Direct3D 11 on Windows), Luau/Python "Custom Topics", Widget plugins and a browser build — [release 4.1.0](https://github.com/PlotJuggler/PlotJuggler/releases/tag/4.1.0)
- RaceCapture App: forum says the built-in analysis view compares laps between sessions (including on phones/tablets) and overlays laps from two drivers — [ASL forum p=24930](https://direct.forum.autosportlabs.com/viewtopic.php?p=24930); the first beta was "basic charting and data over laps" — [ASL forum p=23441](https://direct.forum.autosportlabs.com/viewtopic.php?p=23441); iOS listing: in-app analysis to import log files and view lap data, auto track detection — [App Store](https://apps.apple.com/us/app/-/id1162797255)
- MegaLogViewer HD: compare mode overlays a second file; custom calculated fields/formulas ("Advanced Math"); lap features, track map and video not mentioned on the product page (page footer ©2006-2011, may be stale) — [EFI Analytics](https://www.efianalytics.com/MegaLogViewerHD/)
- Small/new GitHub projects found (all tiny, not mature): caezium/stint (AiM .xrk analysis with laps, splits, corners, G-G, math channels; no licence shown, 4 stars) — [stint](https://github.com/caezium/stint); tatewamola-web/lapsmith (MIT, sim-racing, ghost playback, 4 stars) — [lapsmith](https://github.com/tatewamola-web/lapsmith); Shen-18/SCUT-Racing-Telemetry (student team, no licence shown, 5 stars) — [SCUT](https://github.com/Shen-18/SCUT-Racing-Telemetry); ryzingTitan/obdtrak (GPL-3.0, track-day telemetry app, 1 star) — [obdtrak](https://github.com/ryzingTitan/obdtrak)
- FastF1 is built around F1 timing/telemetry APIs. Its lap-comparison approach (resample telemetry by distance, compare) is the reusable part — [Fast-F1](https://github.com/theOehrly/Fast-F1)

### Inferences
- Feature parity against i2 Pro: TDA ≈ overlay ✔, time slip ✔, GPS line map ✔, math ✔ (basic), video ✔ (manual align), sectors ✔ only on unreleased main. PlotJuggler: overlay by time only, math ✔ (Lua/Python), no map/time slip/laps. RaceCapture App: lap compare ✔, other items unconfirmed. MegaLogViewer HD: math ✔, file compare ✔, rest ✗/unknown.
- Our logger stamps video with GNSS time, so we could compute the TDA video offset automatically. TDA has an `estimate_lap_offset` helper in ui/video.py, but its input is unclear; for now, assume manual alignment for our files.
- Features we already have (lap table, lap video clips, race report) overlap TDA only partly. TDA adds interactive distance overlay, time slip, multi-lap GPS line and math, which are the gaps against i2 Pro. Porting those algorithms (MIT) into our Python backend and drawing them with uPlot/ECharts + Leaflet is licence-clean.
- Unless a tool is specifically lap-aware, "overlay by distance" needs a distance channel computed per lap (from GPS speed integration or lat/lon). TDA's `data/distance.py` and FastF1-style resampling are both references for this.

### Gaps
- No hands-on test of any tool with our data. Feature statements come from READMEs and source file names.
- RaceCapture App: track map line comparison, time slip and video sync not confirmed from a primary source.
- Grafana for post-session: no lap overlay/time slip panel was researched here. As a time-series dashboard it lacks lap/distance concepts unless we pre-compute them. That conclusion is from general knowledge, not a cited source.
- Web chart library specifics (uPlot performance figures, Plotly bundle size, ECharts' large-data mode) were not fetched. Only licences and activity were verified.

## Q4. Ease for non-programmer team members (installer, Japanese UI)

### Takeaway
TDA and PlotJuggler both have ready Windows installers. TDA's last binary is old (v0.4.1, Feb 2024), so the newer features on main need a source install (Python 3.10 + libmpv by hand), which is not realistic for non-programmers. No candidate showed Japanese UI support. MegaLogViewer HD is a paid commercial installer.

### Cited Findings
- TDA releases: v0.1.0 (2024-02-04) to **v0.4.1 (2024-02-25)**, each with `Track.Data.Analysis-x.y.z-win64.msi` (+ arm64 .dmg). The installer adds a Start-menu shortcut "Track Data Analysis" — [Releases](https://github.com/racer-coder/TrackDataAnalysis/releases); [README](https://github.com/racer-coder/TrackDataAnalysis)
- TDA source install on Windows: Python 3.10 from python.org, `pip install -r requirements.txt`, and manually installing libmpv (`libmpv-2.dll` under `ui/`) — [README](https://github.com/racer-coder/TrackDataAnalysis)
- TDA claims high-DPI support and a responsive UI on 2-hour 100 Hz logs on a 10-year-old PC — [README](https://github.com/racer-coder/TrackDataAnalysis)
- PlotJuggler 4.1.0 assets: `PlotJuggler-4.1.0-Windows-x64.exe`, `...-Windows-x64-portable.zip`, AppImage, .deb — [release 4.1.0](https://github.com/PlotJuggler/PlotJuggler/releases/tag/4.1.0). The x64 .exe "installs for the current user, so no administrator rights are needed" — [README](https://github.com/facontidavide/PlotJuggler)
- MegaLogViewer HD: free trial download, Windows/Mac/Linux listed — [EFI Analytics](https://www.efianalytics.com/MegaLogViewerHD/)

### Inferences
- For handing out today: the TDA v0.4.1 MSI (overlay, time slip, map, video, basic math, no sector table) plus our RaceCapture-format .log export. A short Japanese how-to sheet would be needed.
- Asking upstream for a fresh release, or building an MSI from main ourselves with cx_freeze (setup.py is already set up), would give the sector table and track editor. If we redistribute our own build, we take on the libmpv licence question from Q1.
- PlotJuggler is the easiest install, but it does not answer lap questions. Better suited to CAN/sensor debugging than driver coaching.

### Gaps
- Japanese UI / translation support: no evidence found for TDA, PlotJuggler, asammdf GUI or MegaLogViewer HD. TDA's source did not show any i18n hooks in the files skimmed (not exhaustively checked).
- Whether the TDA v0.4.1 MSI runs on current Windows 11 without issues: not tested.

## Q5. Maintenance status (latest release/commit, stars, activity)

### Takeaway
PlotJuggler, asammdf, FastF1, uPlot, ECharts, Plotly.js, Leaflet and Grafana are healthy, actively maintained projects. TrackDataAnalysis is a small single-maintainer project. Its code is active (40 of the last 100 commits since Nov 2025, PySide6 port in 2026), but it has published no binary since Feb 2024. Autosport Labs' open-source repos look dormant or archived.

### Cited Findings
- TDA: 66 stars, 10 forks, 1 open issue; last commits 2026-08-21 "ui/timedist: Disallow zero or negative zoom windows", 2026-08-15 "data/ecumaster: Add support for EMUPROLOG files"; branches `main` and `pyside6`; 40 commits since 2025-11-01; issues include a 2026-04-28 PR "PySide6 port + Mac ARM support, new components, UI/UX polish" (closed) and a 2026-01-21 open issue "VBOX file format not compatible?" — [repo](https://github.com/racer-coder/TrackDataAnalysis); [commits](https://github.com/racer-coder/TrackDataAnalysis/commits/main); [issues](https://github.com/racer-coder/TrackDataAnalysis/issues)
- PlotJuggler: 4.0.0 (2026-09-21) and 4.1.0 (2026-11-05, "171 commits since 4.0.0") — [releases](https://github.com/PlotJuggler/PlotJuggler/releases)
- asammdf 8.8.33 released 2026-11-11 — [asammdf](https://github.com/danielhrisca/asammdf)
- FastF1 v3.9.2 2026-11-02; Plotly.js v4.3.0 2026-11-10; ECharts 6.1.0 2026-05-19; uPlot pushes on 2026-11-14 (last tag 1.6.32, 2025-03); Grafana v13.3.1 2026-11-10 — [FastF1](https://github.com/theOehrly/Fast-F1); [plotly.js](https://github.com/plotly/plotly.js); [echarts](https://github.com/apache/echarts); [uPlot](https://github.com/leeoniya/uPlot); [grafana](https://github.com/grafana/grafana)
- Autosport Labs: firmware archived (2022), RaceAnalyzer last push 2014, RCP2GEMS 2015; a `racecapture_video_data_livestreaming` repo was pushed 2026-10-07 — [autosportlabs org](https://github.com/autosportlabs)

### Inferences
- TDA is a bus-factor-1 project. Embedding its ideas (copying MIT code into our repo) is lower risk than depending on its releases.
- uPlot (small, fast, MIT) or ECharts (Apache-2.0, richer) are both safe long-term choices for adding interactive distance overlay / time slip to our browser UI, with Leaflet (BSD-2) for the GPS line map. Plotly.js is MIT too but heavier (bundle size not verified here).

### Gaps
- No HP Academy / Rennlist forum mentions were collected (searches did not surface them within the tool budget). Community adoption of TDA is unknown beyond 66 stars.
- No other mature OSS "pitwall"-style post-session lap analysers turned up in GitHub searches ("motorsport data analysis", "racing telemetry analysis", "track day telemetry"). Results were mostly F1 / sim-racing hobby projects with fewer than 10 stars.
