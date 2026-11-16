# Video + logged data tools for a self-built logger (sync playback and overlay rendering)

Context for the reader: our logger writes a post-session CSV (GNSS 10 Hz lat/lon/speed, CAN RPM/throttle/temps, IMU, laps) and H.264 video in MPEG-TS (MP2 audio) with gauges already burned in, timestamped in GNSS/UTC. Research date: 2026-11-14. 17 tool calls; several vendor pages blocked (403/404), so some items are marked unverified.

## Q1. Which tools accept data from a non-vendor / self-built logger, in which formats, and is the format spec public?

### Takeaway
The tools with a **public, documented import format** that our CSV can be converted to are: RaceRender (generic CSV spec), Telemetry Overlay (Custom CSV spec with a `utc (ms)` column), and RaceLogic VBO (public developer tutorial; read by Circuit Tools and by TrackDataAnalysis). TrackDataAnalysis does not list plain CSV as an import, so a VBO export would be the route. AiM Race Studio 3 is effectively closed to non-AiM video. DashWare is discontinued.

### Cited Findings
- **RaceRender**: accepts text spreadsheet files (CSV / tab / semicolon, .csv or .txt, ASCII or UTF-8). Only `Time` is required (seconds, or `hh:mm:ss.nn`, first sample need not be zero; alternatively `GPS Time` in raw ms); rows must be chronological. Recommended columns: `Longitude`, `Latitude`, `Altitude`, `GPS_Update`, `Accuracy`, `X` (long G), `Y` (lat G), `MPH`/`KPH`/`Speed (m/s)`, `Heading`, `Lap`, `RPM`, `Gear`, `Throttle`. Extra columns feed custom gauges. With `# RaceRender Data` as first line you can add precise lap times (`# Lap N: hh:mm:ss.nn`) and a `GPS_Delay` column. The page says nothing about UTC/date handling or time-based video sync. — [RaceRender Developer: Data Format](https://racerender.com/Developer/DataFormat.html)
- RaceRender lists data formats CSV, VBO, NMEA, GPX, TCX, FIT "and others". — [RaceRender 3 Features](https://racerender.com/RR3/Features.html)
- **Telemetry Overlay Custom CSV**: comma-separated, dot decimals; header row must include at least one time column: `utc (ms)` (Unix ms), `date` (ISO `YYYY-MM-DDTHH:mm:ss.sssZ`), `time (ms)`, `time (s)`, or `timecode`. Position headers `lat (deg)`, `lon (deg)`, `alt (m)`; optional `speed (m/s)`. Units in parentheses; `(text)` forces a text column. Other columns become custom numeric gauges or Dynamic Text. — [Telemetry tools for Custom CSV](https://goprotelemetryextractor.com/tools-for-custom-csv); corroborated by [Telemetry Overlay manual (PDF)](https://goprotelemetryextractor.com/docs/telemetry-overlay-manual.pdf) (via search snippet)
- Telemetry Overlay also lists RaceChrono CSV, GPX, KML, FIT among inputs. — [manual mirror, manuals.plus](https://manuals.plus/gopro/telemetry-overlay-manual) (secondary)
- A third-party converter for Race-Keeper data states that the `utc (ms)` column "enables automatic sync with video files in Telemetry Overlay". — [sam-dumont/rkd-telemetry-extractor](https://github.com/sam-dumont/rkd-telemetry-extractor) (search snippet; third-party claim)
- **VBO (RaceLogic)**: public developer tutorial. Plain text (UTF-8/ANSI, CRLF), required sections: date/time line, `[header]`, `[channel units]`, `[column names]`, `[data]`; optional `[comments]`, `[laptiming]`, `[avi]`, `[circuit details]`, `[session data]`. Time is `hhmmss.sss` (page does not state UTC explicitly). Lat = minutes x 100000; long = minutes x -100000 (hemisphere reversed). Space-separated fixed-width numeric data. — [RaceLogic developers: VBO file structure](https://developers.racelogic.co.uk/Portal/Tutorials/tutorialVBOfilestructure.html)
- **TrackDataAnalysis** (racer-coder, MIT): natively opens AiM XRK, MoTeC LD, ECUMaster ADULOG/EMUPROLOG, Autosport Labs (RaceCapture) LOG, RaceLogic VBOX (VBO), Race Technology RUN, MegaLogViewer MLG, iRacing IBT. Plain CSV is not listed. — [GitHub racer-coder/TrackDataAnalysis](https://github.com/racer-coder/TrackDataAnalysis)
- **Track Attack**: a user reports exporting CSV from another tool and importing that CSV into Track Attack; no official CSV spec found. Free tier excludes external video import/sync. — [Rennlist thread](https://rennlist.com/forums/data-acquisition-and-analysis-for-racing-and-de/1114136-trackattack-io-use-black-friday-sale.html); [App Store listing](https://apps.apple.com/dk/app/track-attack/id1557802135) (via search snippets)
- **AiM Race Studio 3**: forum posts say RS3 imports video only from AiM SmartyCam; the common GoPro workaround is to export CSV from AiM and render with RaceRender. — [KartPulse forum](https://forums.kartpulse.com/t/camera-what-to-buy-and-some-practical-concerns/3070?page=2); [aimshop RSA3 tutorial 12](https://www.aimshop.com/pages/race-studio-analysis-3-tutorial-12-video-data-together-in-rsa3) (via search snippets). TrackDataAnalysis README also states "AiM only supports SmartyCam video files". — [GitHub README](https://github.com/racer-coder/TrackDataAnalysis)
- **DashWare**: listed as discontinued, last version 1.9.1 (2017), Windows only. — [AlternativeTo](https://alternativeto.net/software/dashware/about) (secondary; no official notice found). Historically accepted TrackAddict CSV and GoPro MP4. — [HP Tuners forum](https://forum.hptuners.com/showthread.php?p=462424)
- **Licence**: RaceRender data-format page shows only a copyright notice, no restriction on third-party data. — [RaceRender Developer](https://racerender.com/Developer/DataFormat.html). TrackDataAnalysis is MIT. — [GitHub](https://github.com/racer-coder/TrackDataAnalysis)

### Inferences
- Writing two exporters from our CSV would cover most tools: (1) a **VBO exporter** (feeds Circuit Tools, TrackDataAnalysis, RaceRender, probably Track Attack) and (2) a **Telemetry Overlay Custom CSV** with `utc (ms)` (we already have UTC). RaceRender can also read a lightly renamed version of our CSV directly.
- Since TrackDataAnalysis also reads Autosport Labs LOG and our project is RaceCapture-compatible, a RaceCapture-style log might be a second route into it (not verified against our actual files).
- No licence restriction similar to MoTeC i2's "non-MoTeC data" clause was found for RaceRender, Telemetry Overlay, Circuit Tools or TrackDataAnalysis, but EULAs were not read in full (see Gaps).

### Gaps
- Circuit Tools EULA / whether it restricts non-VBOX data: vendor pages returned 403; not verified.
- RaceChrono: whether it can import data from an external self-built logger file (rather than recording itself) was not researched. From prior knowledge (unverified here), RaceChrono offers a public BLE "DIY" device API for live CAN/GPS input; this would make our logger a live source rather than a file import.
- Harry's LapTimer, GoPro Quik/Player, Garmin Catalyst: not researched within the call budget; GoPro desktop tools (Studio, Quik desktop) are reported discontinued by secondary blogs only.

## Q2. How is sync done (GPS/UTC, file time, audio pulse, manual)? Can it be saved? Two-lap side-by-side video?

### Takeaway
Only Telemetry Overlay (via `utc (ms)`), Track Attack ("auto sync from any video source", mechanism undocumented) and RaceLogic VBO (sync channels embedded in the data) offer something close to automatic sync for third-party data. TrackDataAnalysis and RaceChrono (for non-GoPro/VIRB cameras) are manual. Side-by-side two-lap video is confirmed only in TrackDataAnalysis-style distance-mode lap playback (one video per log) and RaceRender's split-screen layouts; Circuit Tools dual-video was not verified.

### Cited Findings
- **TrackDataAnalysis**: "any video file", but only one video per log file. Alignment is manual: put cursor at a lap start, right-click "Set video alignment", drag the slider until the frame matches. In distance mode, playback of the alternate lap is sped up/slowed to stay in sync. Motivation: MoTeC playback choppy for 1080p/60 on a 2024 laptop. — [GitHub README](https://github.com/racer-coder/TrackDataAnalysis)
- **VBO video linkage**: `[avi]` section gives base file name of the video files that correspond to the VBO; `avifileindex` and `avisynctime` are standard channels (example values `0001`, `000000266`; meaning/units not stated on the page). — [RaceLogic VBO file structure](https://developers.racelogic.co.uk/Portal/Tutorials/tutorialVBOfilestructure.html). A single VBO can map to multiple AVI files after long recordings. — [Racelogic file formats KB](https://en.racelogic.support/Knowledge_Base/File_Formats) (search snippet)
- **Circuit Tools with third-party video**: release notes list ".vbo and associated .avi files / .vbo and associated .mp4 files" as compatible. — [Circuit Tools 3 release notes](https://vboxmotorsport.co.uk/en/fw-sw/release-notes-circuit-tools-3) (search snippet; page 403 on fetch). Forum: if MP4 is not declared in the VBO, CT assumes AVI; header must reference `avisynctime` not `avitime`; data starting before video breaks sync; a RaceChrono VBO export with bad index values (`avifileindex 0000`, `aviseektime -00000001`) crashed CT. — [RaceChrono forum 1395](https://racechrono.com/forum/discussion/1395/vbo-video-sync-messed-up-when-exporting-whole-session); [RaceChrono forum 2358](https://www.racechrono.com/forum/discussion/2358/vbo-video-export-crashes-circuit-tools-with-index-exception); [RaceChrono comment 8449](https://racechrono.com/forum/discussion/comment/8449/). An older Rennlist post said third-party camera linking was not possible. — [Rennlist](https://rennlist.com/forums/data-acquisition-and-analysis-for-racing-and-de/946828-how-to-get-video-and-data-from-porsche-track-precision-app-in-circuit-tools.html) (likely outdated, conflicts with MP4 support above)
- **Telemetry Overlay**: can "sync telemetry from multiple sources" and merge consecutive videos. — [goprotelemetryextractor.com](https://goprotelemetryextractor.com/). The exact rule for matching `utc (ms)` to a non-GoPro video (e.g., MP4 creation_time metadata) is not documented on the pages fetched. — [Custom CSV page](https://goprotelemetryextractor.com/tools-for-custom-csv)
- **Track Attack**: described as automatically syncing data to video "from any video source"; users say auto-sync works well. — [Rennlist / HP Academy threads via search](https://www.hpacademy.com/forum/data-analysis-fundamentals/show/racecapture/) (secondary)
- **RaceChrono**: auto-sync only for GoPro and Garmin VIRB recorded with camera GPS on (v6.0+); others via manual sync adjustment; one user found auto-sync ~2 s off. Video files must sit in specific folders. — [RaceChrono tutorial 480](https://racechrono.com/article/480); [RaceChrono article 2059](https://racechrono.com/?p=2059); [forum 13325](https://racechrono.com/forum/discussion/comment/13325/); [forum 8874](https://racechrono.com/forum/discussion/comment/8874/)
- **AiM RS3**: side-by-side two-video comparison was in beta per Rennlist posts (status at late 2026 unverified). — [Rennlist AiM thread](https://rennlist.com/forums/data-acquisition-and-analysis-for-racing-and-de/1040364-aim-smartycam-sync-with-mxl2-data.html); AiM FAQ on movie comparison exists: [FAQ_RS3_MoviesComparison (ita PDF)](https://aimsports.com/download/faqs/ita/software/rs3/FAQ_RS3_MoviesComparison_100_ita.pdf) (not read)
- **RaceRender**: "Trimming and Synchronization Tools"; multi-camera picture-in-picture, split-screen and quad layouts in all editions. Whether sync is automatic is not stated. — [RaceRender 3 Features](https://racerender.com/RR3/Features.html)

### Inferences
- Because our video already carries GNSS/UTC timestamps, the most reliable path for automatic sync into Circuit Tools is to **write `avifileindex`/`avisynctime` ourselves** in a VBO export (we know each frame's UTC). Units of `avisynctime` (likely ms into the video file) must be confirmed against a real VBOX Video file before relying on it.
- For Telemetry Overlay, providing `utc (ms)` plus correct MP4 `creation_time` metadata (set at remux time) is the plausible route to automatic sync; needs a hands-on test.
- TrackDataAnalysis's manual alignment is a one-off per log; whether the alignment is saved with the session was not stated in the README (see Gaps).
- Since our app (EcoLogger PC app, SP-5-2) already parses laps and UTC, an in-house "cursor-to-video" player using the absolute timestamps may be simpler than fighting third-party sync quirks; this is a design inference, not a researched finding.

### Gaps
- Whether TrackDataAnalysis persists the video offset (likely in its metadata DB, not confirmed).
- Whether Circuit Tools 3 supports dual-video lap comparison with non-VBOX video; vendor support pages could not be read (403 / article body missing).
- Track Attack's actual sync mechanism (GPS in camera metadata? file timestamps?) undocumented in sources found.
- No source described audio sync-pulse methods for any of these tools.

## Q3. Video formats (MP4/H.264, MPEG-TS), 1080p performance

### Takeaway
MPEG-TS input is not documented for any of the tools checked; MP4/H.264 is the safe target. TrackDataAnalysis uses libmpv and accepts "any video file", so it is the most likely to play our TS directly, and it was built specifically because 1080p/60 playback was choppy in MoTeC.

### Cited Findings
- TrackDataAnalysis: "any video file"; install requires libmpv; written because MoTeC 1080p/60 playback was choppy. — [GitHub README](https://github.com/racer-coder/TrackDataAnalysis)
- Circuit Tools: .avi and .mp4 associated with .vbo. — [CT3 release notes (snippet)](https://vboxmotorsport.co.uk/en/fw-sw/release-notes-circuit-tools-3); [Circuit Tools macOS release notes (snippet)](https://www.vboxmotorsport.co.uk/index.php/en/fw-sw/release-notes-circuit-tools-macos)
- RaceRender: "many popular video file formats", none named; MPEG-TS not mentioned. — [RaceRender 3 Features](https://racerender.com/RR3/Features.html)
- RaceChrono: export failures reported with an external camera's audio format and with 4K/large files. — [forum 8980](https://racechrono.com/forum/discussion/comment/8980/); [forum 13267](https://racechrono.com/forum/discussion/comment/13267/)

### Inferences
- Plan for a lossless **TS -> MP4 remux** (copy H.264 stream, transcode MP2 audio to AAC, or drop audio) as part of the collection step; MP2 audio is a likely trouble spot given RaceChrono's audio-format failure reports.
- The burned-in gauges reduce the need for overlay rendering; the main value of third-party tools for us is synced analysis playback, not rendering.

### Gaps
- No tool documentation confirms MPEG-TS or MP2 audio support; needs hands-on testing.
- No published 1080p performance figures for Circuit Tools, Track Attack or Telemetry Overlay.

## Q4. Cost, platforms, maintenance status

### Takeaway
Free options: TrackDataAnalysis (MIT, Win/Linux/Mac, active), Circuit Tools (believed free, unverified), RaceRender Free (3-min limit, watermark). Paid: RaceRender 3 $39.95-$59.95, Telemetry Overlay $199 one-time (shown reduced from $299) with 1 year of updates, Track Attack Pro subscription (~$80/yr, dated). DashWare dead since 2017.

### Cited Findings
- RaceRender 3: Free (output capped at 3 min, full logo, 6 inputs, 32 objects), Deluxe $39.95, Advanced $49.95, Ultimate $59.95; Windows and macOS; latest listed version 3.7.3, page copyright 2022 (no release date shown). — [RaceRender 3 Features](https://racerender.com/RR3/Features.html); changelog: [Softpedia RaceRender changelog](https://www.softpedia.com/progChangelog/RaceRender-Changelog-119650.html) (not read)
- Telemetry Overlay: $199 one-time (shown next to $299), "use forever", 1 year updates/support; Windows 10/11, macOS (Apple Silicon and Intel), Linux (DEB/RPM). Lap Timer and Sector Times gauges listed. — [goprotelemetryextractor.com](https://goprotelemetryextractor.com/); [Custom CSV page](https://goprotelemetryextractor.com/tools-for-custom-csv). Conflicting third-party prices: $196 one-time — [OVRLEY comparison](https://www.ovrley.cc/telemetry-overlay-software/); free limited + ~$5/month or ~$50/year — [stintbox.app guide](https://stintbox.app/guides/best-telemetry-software). The vendor page fetched 2026-11-14 is treated as authoritative.
- TrackDataAnalysis: MIT; Windows x86_64 and Arm binaries, Ubuntu 22.04+, Mac Arm; latest changelog entry 0.4.1 (bug fixes to 0.4.0); 260 commits; no release date visible on the page. — [GitHub](https://github.com/racer-coder/TrackDataAnalysis)
- Track Attack: Pro ~$80/yr or $8/month per an undated forum post; free edition limited to 25-min sessions, 10 sessions, no external video import/sync. — [KartPulse forum](https://forums.kartpulse.com/t/camera-what-to-buy-and-some-practical-concerns/3070?page=2); [App Store](https://apps.apple.com/dk/app/track-attack/id1557802135)
- DashWare: discontinued, last 1.9.1 (2017), Windows. — [AlternativeTo](https://alternativeto.net/software/dashware/about)
- RaceChrono Pro: iOS/Android app with video linking and overlay export; overlay-only export was on the roadmap per a forum post; workaround blue-screen overlay for compositing. — [forum 13267](https://racechrono.com/forum/discussion/comment/13267/); [forum 2524](https://racechrono.com/forum/discussion/2524/simple-trick-to-export-just-the-overlay-and-composit-it-in-premiere-pro)

### Inferences
- For a student team on Windows + Android with a public repo, TrackDataAnalysis (free, MIT, Windows binaries) plus a VBO exporter is the lowest-cost analysis route; Telemetry Overlay is the most direct paid route for "putting data on video" from our own CSV with UTC.
- RaceRender's last listed version (3.7.3, page (c) 2022) suggests slow maintenance; treat as stable but not actively developed (inference).

### Gaps
- Circuit Tools price/latest version as of late 2026: vendor pages 403; not verified (commonly free download, from prior knowledge only).
- Track Attack current pricing and Windows desktop availability not verified from vendor site.
- TrackDataAnalysis release date of 0.4.1 not visible.

## Q5. Analysis depth (lap overlay, time slip, track map) vs pure overlay rendering

### Takeaway
Analysis tools: TrackDataAnalysis (time slip, multi-lap overlay, distance/time graphs, GPS map with satellite, math channels, lap video in distance mode), Circuit Tools, Track Attack, AiM RS3 (AiM data only). Rendering tools: RaceRender, Telemetry Overlay, DashWare (dead), RaceChrono export. RaceRender sits in between (lap times, multi-camera layouts) but is a renderer, not an analysis suite.

### Cited Findings
- TrackDataAnalysis features: time slip; multi-lap overlay with per-lap offsets; time/distance graphs with zoom/pan; GPS track map with optional satellite background; channel value search, math channels, metadata DB. — [GitHub](https://github.com/racer-coder/TrackDataAnalysis)
- Circuit Tools 3 menus include Laps & Sessions, Channels, Maths, Reports, Measure, Insights & Track Report, Track (no menu labelled Video in CT3 toolbar navigation; separate Video sections exist for CT macOS/iOS). — [Racelogic support: CT3 toolbar](https://support-centre.racelogic.co.uk/motorsport/software/ct3/ug/toolbar/)
- RaceRender: precise lap times via `# Lap` tags; overlay objects; multi-camera layouts. — [Developer Data Format](https://racerender.com/Developer/DataFormat.html); [RR3 Features](https://racerender.com/RR3/Features.html)
- Telemetry Overlay: gauges incl. Lap Timer, Sector Times; no lap comparison or analysis graphs listed on the product page. — [goprotelemetryextractor.com](https://goprotelemetryextractor.com/)

### Inferences
- Benchmark against MoTeC i2 Pro (excluded for licence): TrackDataAnalysis is the closest free equivalent for cursor-scrub + video, but limited to one video per log and manual alignment.
- For "quick analysis + easy video", a split approach fits: TrackDataAnalysis (or our own app) for analysis, Telemetry Overlay / RaceRender only when a shareable rendered video with extra overlays is needed (rarely, since gauges are already burned in).

### Gaps
- Circuit Tools' current video/lap-comparison feature set for third-party MP4 could not be read from primary docs.
- Garmin Catalyst, Harry's LapTimer, GoPro Player telemetry not evaluated (call budget).
