# Desktop motorsport data-analysis software usable with self-built logger data (Windows), as of 2026-11

Scope: candidates other than MoTeC i2 Pro (excluded for licence reasons; used only as feature benchmark). Research done 2026-11-14 via web search/fetch. Several vendor pages returned HTTP 403 to automated fetch (vboxmotorsport.co.uk, racelogic.support, xtramotorsport.com), so some VBOX/WinDarab-price facts rest on search snippets and are marked accordingly.

## Q1. Licence/EULA: is use with non-vendor / self-built logger data permitted? Any paid import feature?

### Takeaway
Only two products have an explicit, vendor-stated route for third-party data: Bosch WinDarab (official FAQ: non-Bosch data may be imported as ASCII or MDF, Free edition included) and the MIT-licensed open-source Track Data Analysis (no EULA restriction by definition). GEMS GDA allows CSV import but only in the paid Professional edition; Cosworth Pi Toolbox's free Lite tier is documented only for iRacing data. AiM RS3, Race Technology Analysis and VBOX Circuit Tools are free but no documented generic import of foreign data was found, so "using them with our data" would mean imitating their proprietary/native formats, which is the same category of risk as the MoTeC .ld case unless the vendor confirms otherwise.

### Cited Findings
**Benchmark / the problem being avoided (MoTeC i2)**
- A MoTeC staff forum reply (2009) said MoTeC does not release the .ld format and that creating .ld files to use in i2 "would be in breach of the licence agreement which you agree to when you install i2"; MoTeC was then considering selling licence keys to import other formats without MoTeC hardware — [MoTeC forum p=2241 (via search summary; forum now redirects to motec.zendesk.com)](https://forum.motec.com.au/viewtopic.php?p=2241)
- Forum posts paraphrase the i2 terms as barring use with data generated "directly or indirectly" by non-MoTeC products unless that product is MoTeC-licensed (user paraphrase, not verified against current EULA text) — [MoTeC forum p=2241 search summary](https://forum.motec.com.au/viewtopic.php?p=2241); a RaceDepartment commenter: "The use of i2 with non licensed data exporters is not allowed" — [RaceDepartment](https://racedepartment.com/threads/telemetry-tool-for-ams2.187091/page-5)
- MoTeC staff (2015) described an "Open Standard Log File" licence for i2 Pro that would allow opening standard log files (status/price today unverified) — [MoTeC forum search summary](https://forum.motec.com.au/viewtopic.php?p=13366); MoTeC also publishes an i2 API user guide — [i2 API User Guide PDF](https://www.motec.com.au/hessian/uploads/i2_API_User_Guide_330ed28c83.pdf)

**Bosch WinDarab (Free / Expert) — explicit permission for non-Bosch data**
- Official Bosch page FAQ: "Yes, it is possible to import and analyze ASCII or MDF files." (answer to whether non-Bosch data can be used) — [Bosch Motorsport WinDarab page](https://www.bosch-motorsport.com/products-and-services/software-highlights/windarab/)
- Product page lists "ASCII import and export" among features — [Bosch WinDarab page (search summary)](https://www.bosch-motorsport.com/products-and-services/software-highlights/windarab/)
- Free licensing: no immediate key, registration required within 20 days; "After registration, you can continue using WinDarab Free indefinitely." Expert needs a licence key (Tools > Update license, internet required) — [Bosch WinDarab page](https://www.bosch-motorsport.com/products-and-services/software-highlights/windarab/)
- WinDarab wiki legal text: "The License Agreement entitles you to work with this software. You may not, however, run this software concurrently on different computers."; reproduction/distribution needs "prior written consent of Robert Bosch GmbH". No clause restricting the data source was found on that page — [WinDarab V7 Wiki legal page](https://www.bosch-motorsport.com/content/downloads/WinDarab_Wiki/en-GB/239848075.html)
- Data sheet: Free limited to 4 open files, Expert unlimited; data sheet also mentions export restrictions for some countries — [WinDarab V7 data sheet (search summary)](https://www.bosch-motorsport.com/content/downloads/Raceparts/Resources/pdf/Data%20Sheet_70956555_Analysis_Tool_WinDarab_V7.pdf)

**GEMS Data Analysis (GDA)**
- "Standard is provided free of charge with all GEMS data loggers"; Professional adds CSV and Matlab import/export; page says GDA is compatible with "all current GEMS data loggers and logging displays" and does not mention third-party loggers — [GEMS GDA product page](https://gems.co.uk/products/software/gda/)
- GEMS engineer (2013): CSV import "is only available in GDA-Pro" — [GEMS forum: CSV import/export](https://www.gems.co.uk/gemsforum/viewtopic.php?p=1519); 2014 thread: a CSV import bug in newly purchased GDA Pro, fixed by a beta build — [GEMS forum: Importing CSV error](https://www.gems.co.uk/gemsforum/viewtopic.php?p=1728)
- Legacy route: Autosport Labs' RCP2GEMS converts RaceCapture/Pro CSV for import into GEMS' Dlog99 then saving .stf for GDA; a user reported Dlog99 is no longer downloadable from GEMS — [RCP2GEMS GitHub](https://github.com/autosportlabs/RCP2GEMS); [Autosport Labs forum](https://direct.forum.autosportlabs.com/viewtopic.php?p=20050)
- No EULA text for GDA was found online.

**Cosworth Pi Toolbox (Lite free / Plus / Pro / Ultra)**
- "'Lite' remains free of charge"; subscription billing only on v14; page lists "Native iRacing .ibt/.blap/.olap support"; CSV not mentioned; pricing via sales — [Cosworth Pi Toolbox page](https://www.cosworth.com/motorsport/products/pi-toolbox)
- Tier model: "each license builds on the previous ... Lite, Plus, Pro, Ultra" — [Pi Toolbox product information PDF (search summary)](https://www.cosworth.com/media/2erfisc1/pi-toolbox-product-information-v2.pdf)
- Third-party converter vendor says importing its converted data "requires a Cosworth Pi Toolbox Pro or Ultra version" (vendor claim, unverified by Cosworth) — [RaceDataConverter listing](https://www.digistore24.com/product/545921)
- A Pi ASCII importer exists (forum mention, licence tier not stated) — [MoTeC forum: Importing CSV's](https://forum.motec.com.au/viewtopic.php?p=19680)

**AiM Race Studio 3 Analysis**
- RS3 release notes (latest 3.85.12, Nov 12 2026) mention imports only from simulators (Assetto Corsa/ACC, iRacing); CSV appears only as an export format; no VBO / other-logger import; nothing on licensing of imports — [RS3 release history](https://docs.aim-sportline.com/racestudio3/html/release/software-release.html)
- Community: "Aim has native CSV export" (export direction only) — [Rennlist AiM to MoTeC thread](https://rennlist.com/forums/data-acquisition-and-analysis-for-racing-and-de/1246322-aim-to-motec-2.html); Race Studio 2 once imported Traqmate .tqm files (RS2, not confirmed for RS3) — [Rennlist](https://rennlist.com/forums/data-acquisition-and-analysis-for-racing-and-de/1031039-aim-can-import-trackmate-data.html)

**Race Technology Analysis (V10)**
- Free download, "the main application that comes with nearly all Race Technology products"; no statement on importing non-RT data — [Race Technology analysis software page](https://race-technology.com/gb/racing/software/analysis-software)
- Current version 10.0.0438, published Jan 6, 2026; V10 drops legacy DL1 MK2/VIDEO4 (V8.5 still available); export to CSV/.M/.MAT/text documented, no CSV import found — [search summary of race-technology.com wiki/downloads](https://race-technology.com/wiki/index.php/Software/AnalysisV10)

**RaceLogic VBOX Circuit Tools 3**
- "completely free to download and use, with no subscriptions or paywalls" (search snippet; page 403 to fetch) — [VBOX Circuit Tools (US)](https://vboxmotorsport.co.uk/us/circuit-tools)
- Installer presents an EULA that must be accepted (macOS release notes; EULA text not retrieved) — [Circuit Tools macOS release notes (search summary)](https://vboxmotorsport.co.uk/en/fw-sw/release-notes-circuit-tools-macos)
- Racelogic publishes the VBO text-file structure on its Developer Portal (sections, formats, standard channels); the page carries a Racelogic copyright notice and contains no licence terms either permitting or forbidding third parties from writing VBO files — [Racelogic Developer Portal: VBO file structure](https://developers.racelogic.co.uk/Portal/Tutorials/tutorialVBOfilestructure.html)
- Third-party apps (e.g., RaceChrono) export VBO for use in Circuit Tools, and users discuss it openly on forums — [RaceChrono forum](https://racechrono.com/forum/discussion/comment/8449/)

**Track Data Analysis (racer-coder, open source)**
- "GUI for analyzing AiM, MoTeC, or RaceCapture data logs"; licence MIT — [GitHub racer-coder/TrackDataAnalysis](https://github.com/racer-coder/TrackDataAnalysis)

**Track Attack**
- Exists as a mobile app plus TrackAttack.io service; external video import/sync is a Pro feature; App Store: Pro $5.99/month, $49.99/year — [App Store listing (search summary)](https://apps.apple.com/app/id1557802135); HP Academy user says TrackAttack.io imports RaceCapture logs — [HP Academy forum](https://www.hpacademy.com/forum/data-analysis-fundamentals/show/racecapture/)

### Inferences
- WinDarab is the strongest "professional, no-licence-problem" candidate: the vendor itself states non-Bosch ASCII/MDF data can be analysed, and the Free edition is permanent after registration. Still, the full EULA text (installer) should be read once before team rollout; it was not retrieved here.
- VBO is a pragmatic second route: the format is published by Racelogic for developers, widely written by third-party apps, and Circuit Tools is free. However, no explicit "you may use non-VBOX data" statement was found; risk is low-but-nonzero until the EULA is read or Racelogic is asked.
- Writing AiM .xrk or Race Technology .run files ourselves to use their free software would be analogous to the MoTeC .ld problem (undocumented proprietary formats, hardware-bundled software) — avoid without written vendor consent.
- Track Data Analysis (MIT) has zero licence risk, but it does not list generic CSV import; we would either export VBO (supported) or add a CSV reader ourselves (allowed by MIT; contributing upstream also possible).
- GDA Pro and Pi Toolbox Pro/Ultra are paid routes that likely permit third-party CSV/ASCII import, but prices and EULA wording were not found; contact vendors.

### Gaps
- Full EULA texts for WinDarab Free, Circuit Tools, GDA, RS3, Race Technology Analysis, Pi Toolbox were not retrieved (installer-embedded or not public). No clause explicitly forbidding non-vendor data was found for any candidate other than MoTeC.
- Whether the MoTeC "Open Standard Log File" licence exists today and its price — unverified.
- Which Pi Toolbox tier allows ASCII/CSV import — not confirmed by Cosworth sources.

## Q2. Cost, seats, and distribution within a student team

### Takeaway
Free with no hardware tie found: WinDarab Free (registration, 4 open files, one machine per licence), VBOX Circuit Tools, Race Technology Analysis, Track Data Analysis (MIT). Free but hardware-tied in wording: GDA Standard ("with all GEMS data loggers"). Paid: GDA Pro, WinDarab Expert, Pi Toolbox Plus/Pro/Ultra, Track Attack Pro (subscription).

### Cited Findings
- WinDarab Free: registration within 20 days, then indefinite use; licence forbids concurrent use on different computers (so each member registers their own copy) — [Bosch WinDarab page](https://www.bosch-motorsport.com/products-and-services/software-highlights/windarab/); [WinDarab wiki legal page](https://www.bosch-motorsport.com/content/downloads/WinDarab_Wiki/en-GB/239848075.html)
- WinDarab Expert price: an XTRA Motorsport article (snippet only; page 403) says "the single-user licence is now under €1,000" and that Expert used to mean a three-seat package — UNVERIFIED snippet — [XTRA Motorsport blog](https://xtramotorsport.com/blog/data-logging/)
- Bosch page gives no prices — [Bosch WinDarab page](https://www.bosch-motorsport.com/products-and-services/software-highlights/windarab/)
- GDA Standard free with GEMS loggers; Pro price not published — [GEMS GDA page](https://gems.co.uk/products/software/gda/)
- Pi Toolbox Lite free; paid tiers via sales; iRacing promotions gave time-limited Plus trials (e.g., 14 days from June 26, 2026) — [Cosworth Pi Toolbox page](https://www.cosworth.com/motorsport/products/pi-toolbox); [iRacing news](https://www.iracing.com/cosworth-pi-toolbox-plus-free-trial-returns-updated-features-for-iracing-spa-24/)
- VBOX Circuit Tools free, no subscriptions — [VBOX Circuit Tools (search snippet)](https://vboxmotorsport.co.uk/us/circuit-tools)
- Race Technology: "All our software is available as a single download ... free download" with free upgrades — [Race Technology analysis software](https://race-technology.com/gb/racing/software/analysis-software)
- Track Data Analysis: MIT licence (free redistribution permitted) — [GitHub](https://github.com/racer-coder/TrackDataAnalysis)
- Track Attack Pro: $5.99/month or $49.99/year (App Store; a KartPulse post quoted $80/yr, likely outdated) — [App Store (search summary)](https://apps.apple.com/app/id1557802135); [KartPulse forum](https://forums.kartpulse.com/t/camera-what-to-buy-and-some-practical-concerns/3070?page=2)

### Inferences
- For a student team, the cleanest distribution model is: each member downloads WinDarab Free / Circuit Tools / Track Data Analysis themselves from the vendor/GitHub; the team distributes only its own data files and workbooks/layouts. Redistributing the WinDarab installer itself needs Bosch consent per the wiki text.
- If the logger is sold later, recommending WinDarab Free / Circuit Tools to customers is fine as long as each customer obtains the software from the vendor; bundling would need vendor agreement.

### Gaps
- Official WinDarab Expert, GDA Pro, Pi Toolbox tier prices; any academic/student discounts (Bosch/Cosworth often support FS teams, but no source found here).

## Q3. Import formats we would need to export, and whether specs are public

### Takeaway
Best targets: (1) VBO text format for Circuit Tools and Track Data Analysis (spec published by Racelogic); (2) ASCII (and/or ASAM MDF) for WinDarab; (3) plain CSV for GDA Pro. MDF is an ASAM standard with open-source writers (e.g., Python asammdf — not researched here).

### Cited Findings
- VBO structure (Racelogic Developer Portal): date/time line; [header] channel list; [channel units]; optional [comments], [laptiming] (gates), [avi] (video base filename), [circuit details], [session data]; [column names] (no spaces, space-separated); [data] space-separated numeric rows. Time hhmmss.sss; latitude in minutes x100000; longitude in minutes x -100000 (reversed sign convention); CR+LF; UTF-8 or ANSI. Standard channels include satellites, time, latitude, longitude, avifileindex, avisynctime — [VBO file structure](https://developers.racelogic.co.uk/Portal/Tutorials/tutorialVBOfilestructure.html)
- Pitfall: the example header uses `avisynctime` but column name `avitime`; a RaceChrono user found Circuit Tools crashed with the short name and recommends `avisynctime` in both places; also check no stray spaces per line — [Racelogic dev portal](https://developers.racelogic.co.uk/Portal/Tutorials/tutorialVBOfilestructure.html); [RaceChrono forum](https://racechrono.com/forum/discussion/comment/8449/)
- WinDarab imports ASCII or MDF from non-Bosch sources; CSV not named explicitly — [Bosch WinDarab page](https://www.bosch-motorsport.com/products-and-services/software-highlights/windarab/)
- WinDarab V7 operation manual (v1.2, April 2025) exists as PDF and likely documents the ASCII import layout (not fetched) — [Operation Manual 70959883](https://www.bosch-motorsport.com/content/downloads/Raceparts/Resources/pdf/Operation%20Manual_70959883_Analysis_Tool_WinDarab_V7.pdf)
- GDA Pro: CSV and Matlab import; Standard: CAN DBC import — [GEMS GDA page](https://gems.co.uk/products/software/gda/)
- Track Data Analysis native imports: AiM XRK, MoTeC LD, ECUMaster ADULOG/EMUPROLOG, Autosport Labs LOG, RaceLogic VBOX, Race Technology RUN, MegaLogViewer MLG, iRacing IBT; generic CSV not listed — [GitHub](https://github.com/racer-coder/TrackDataAnalysis)
- Autosport Labs (RaceCapture) .log is natively read by Track Data Analysis — relevant because our logger is RaceCapture-compatible — [GitHub](https://github.com/racer-coder/TrackDataAnalysis)
- RS3 Analysis: no generic CSV/VBO import found — [RS3 release history](https://docs.aim-sportline.com/racestudio3/html/release/software-release.html)
- Race Technology: CAN DBC load supported; CSV export only — [Race Technology page](https://race-technology.com/gb/racing/software/analysis-software)

### Inferences
- A single VBO exporter covers both Circuit Tools and Track Data Analysis, and VBO's [avi]/avisynctime fields offer a path to video linking. Because our Ver.2 logger already speaks RaceCapture formats, Track Data Analysis' Autosport Labs LOG reader may work with little or no new export code (needs testing).
- WinDarab ASCII import layout must be confirmed from the V7 operation manual before writing an exporter.

### Gaps
- Exact WinDarab ASCII import layout (header rows, separator, time column, units) — manual PDF not fetched.
- Whether Circuit Tools 3 imports anything other than VBO (e.g., CSV) — official pages 403; search found CSV export only.

## Q4. Features vs MoTeC i2 Pro (overlay, time slip/variance, GPS track map, sectors, math channels, histograms, reports)

### Takeaway
WinDarab Expert and Pi Toolbox Pro are the closest to i2 Pro; WinDarab Free has "all basic functions". Track Data Analysis covers the i2-style core (overlay, time slip, GPS map, math, worksheets, video). Circuit Tools covers overlay/delta/map/video well but is lighter on math channels (unverified).

### Cited Findings
- WinDarab: lap overlay, racetrack creation from v/acc or GPS data, segmentation, user-defined math channels and segment-based math functions, measurement video; "The free version offers all basic functions that are necessary for data evaluation"; Expert "full function range without limitations" — [Bosch WinDarab page](https://www.bosch-motorsport.com/products-and-services/software-highlights/windarab/)
- WinDarab 7.8 / 7.10 updates (file compression, trackmap in BMS2Api, Direct2D oscilloscope, DirectX 11 3D views); no V8 found — [WinDarab V7 Wiki](https://www.bosch-motorsport.com/content/downloads/WinDarab_Wiki/en-GB/304592523.html); [WinDarab V7 Wiki 7.10](https://www.bosch-motorsport.com/content/downloads/WinDarab_Wiki/en-GB/392199435.html)
- GDA: track map (Standard), custom maths (Pro adds user-defined maths), customisable overlays, Pro video — [GEMS GDA page](https://gems.co.uk/products/software/gda/)
- Pi Toolbox: interactive circuit maps, "Pi Math, Constants and Events engine built in" — [Cosworth page](https://www.cosworth.com/motorsport/products/pi-toolbox)
- Track Data Analysis: time/distance graphs with overlaid channels, multiple laps, time slip, channel search and value reports, GPS map with optional satellite background, video playback synced to laps, workspaces/worksheets, math channels, metadata database — [GitHub](https://github.com/racer-coder/TrackDataAnalysis)
- Race Technology Analysis: flexible graphing, track maps, user-defined variables/filtering, "almost unlimited laps and sectors", simulation vs "perfect" driver, CAN DBC, up to 1 kHz — [Race Technology page](https://race-technology.com/gb/racing/software/analysis-software)
- Circuit Tools: single-lap CSV export; video/data sync fixes in release notes (feature list not retrievable due to 403) — [Circuit Tools release notes (search summary)](https://vboxmotorsport.co.uk/en/fw-sw/release-notes-circuit-tools)

### Inferences
- For an endurance/eco-run team, WinDarab Free (4 open files) is enough for comparing a few stints/laps; Expert only needed for many files.

### Gaps
- Histogram/report capabilities per product, Free vs Expert exact feature split for WinDarab, Circuit Tools math-channel support — not confirmed.

## Q5. Video sync

### Takeaway
Documented video sync: GDA Pro ("loading/syncing of video files"), Track Data Analysis ("video playback synced to laps"), Circuit Tools (via VBO avifileindex/avisynctime; users manually edit avisynctime to align external video), Race Technology (GoPro video), WinDarab ("measurement video", sync method not documented online). Sync mechanism details (GPS time vs manual offset) were largely not published.

### Cited Findings
- GDA Professional: video playback with customisable overlay objects, loading/syncing of video files — [GEMS GDA page](https://gems.co.uk/products/software/gda/)
- Circuit Tools: a RaceChrono user aligned external video by editing the VBO avisynctime column; release notes mention fixed video/data sync and improved sync across multiple video files; a single .vbo can link to multiple .mp4 files — [RaceChrono forum](https://racechrono.com/forum/discussion/comment/8449/); [Racelogic file formats KB (search summary)](https://en.racelogic.support/Knowledge_Base/File_Formats)
- Track Data Analysis: video playback synced to laps — [GitHub](https://github.com/racer-coder/TrackDataAnalysis)
- Race Technology: video loaded from GoPro cameras for data/video analysis; overlays for video export — [Race Technology page](https://race-technology.com/gb/racing/software/analysis-software)
- WinDarab: "measurement video" listed; sync method not described — [Bosch WinDarab page](https://www.bosch-motorsport.com/products-and-services/software-highlights/windarab/)
- Track Attack: external video import/sync requires Pro — [App Store (search summary)](https://apps.apple.com/app/id1557802135)

### Inferences
- Since our H.264 video is GNSS-timestamped, writing avifileindex/avisynctime in the VBO (ms offset into the MP4 per sample) should give automatic sync in Circuit Tools without manual offset; our burned-in gauge overlay makes in-tool overlays less critical.

### Gaps
- Exact semantics of avisynctime (units) — not stated on the dev portal page. Supported video containers/codecs for WinDarab, GDA, Track Data Analysis — not found.

## Q6. Platform, Japanese UI, maintenance status

### Takeaway
All candidates run on Windows; Track Data Analysis also Linux/macOS Arm. Actively maintained in 2025-2026: AiM RS3 (3.85.12, 2026-11-12), Race Technology (10.0.0438, 2026-01-06), WinDarab V7 (7.10, 2025 wiki), Pi Toolbox v14, Track Data Analysis (0.4.1, date not shown). No Japanese UI confirmed for any.

### Cited Findings
- AiM RS3 3.85.12, Nov 12 2026 — [RS3 release history](https://docs.aim-sportline.com/racestudio3/html/release/software-release.html)
- Race Technology Analysis 10.0.0438, Jan 6 2026; "Runs under Windows" — [Race Technology](https://race-technology.com/gb/racing/software/analysis-software); [RT wiki (search summary)](https://race-technology.com/wiki/index.php/Software/AnalysisV10)
- WinDarab V7 up to 7.10 (2025 copyright); recommended Windows 10, 16 GB RAM, 1920x1080 — [WinDarab wiki](https://www.bosch-motorsport.com/content/downloads/WinDarab_Wiki/en-GB/392199435.html); [WinDarab wiki legal page](https://www.bosch-motorsport.com/content/downloads/WinDarab_Wiki/en-GB/239848075.html)
- Pi Toolbox v14 (subscription billing), x64 builds — [Cosworth page](https://www.cosworth.com/motorsport/products/pi-toolbox)
- Track Data Analysis 0.4.1; Windows 10+, Ubuntu 22.04+, macOS Arm; 260 commits, 1 open issue — [GitHub](https://github.com/racer-coder/TrackDataAnalysis)
- Circuit Tools: Windows and macOS versions exist — [Circuit Tools macOS release notes](https://vboxmotorsport.co.uk/en/fw-sw/release-notes-circuit-tools-macos)

### Inferences
- English UI should be assumed for all; team members will need short Japanese guides.

### Gaps
- Japanese language support for any product — no source found. Latest GDA version/date and latest Circuit Tools version — not retrieved. Track Data Analysis release date / single-maintainer bus-factor risk — not determined. McLaren ATLAS was not researched (enterprise-licensed, out of reach for this use case; unverified).
