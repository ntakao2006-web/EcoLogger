# Mobile lap-timing / analysis apps and real-time telemetry options for a self-built logger

Research date: 2026-11-14. Scope: apps that can (a) take a self-built logger's data live (BLE / Wi-Fi / NMEA) and (b) import logs after the session on a phone, plus open-source / self-hostable real-time viewers. "Unverified" marks items I could not confirm from a primary source.

## Live input: protocols, documentation, licence/fee, update rate

### Takeaway
RaceChrono has the most open and best-documented path for a self-built device. It offers two public DIY protocols: (1) "RC2/RC3", a text extension of NMEA 0183 sent over Bluetooth RFCOMM or TCP/Wi-Fi, and (2) a BLE GATT API for GPS and CAN frames that is published on GitHub with reference Arduino devices. TrackAddict also publishes its own text protocol (NBP, over Bluetooth SPP, Wi-Fi TCP or USB). Harry's LapTimer accepts any NMEA 0183 GPS, and its top edition already speaks the RaceCapture protocol. Its general developer/sensor API is not publicly documented. None of these vendors publishes explicit licence terms for implementing their protocol, and I found no fee.

### Cited Findings
**RaceChrono: DIY protocols**
- RaceChrono's DIY tutorial lists three device APIs. (1) RC2/RC3 is "a RaceChrono extension to NMEA 0183" that can be mixed with standard $Gxxxx GPS sentences or used alone. (2) Bluetooth LE "GPS" and "CAN-Bus" APIs. (3) The standard NMEA 0183 checksum. All three are configured via Settings > Add other device > RaceChrono DIY. — [RaceChrono DIY tutorial](https://racechrono.com/article/2572)
- RC2/RC3 transports: Bluetooth RFCOMM and TCP/IP (Wi-Fi) on Android; TCP/IP only on iOS. — [RaceChrono DIY tutorial](https://racechrono.com/article/2572)
- RC2 fields: timestamp, count, 3-axis accelerometer, rpm/d1, d2 and analog a1–a8. RC3 adds a 3-axis gyro and extends analog to a1–a15. Values run ±2,000,000.000, accelerometer is in G and gyro in deg/s, lines end in CR+LF. — [RaceChrono DIY tutorial](https://racechrono.com/article/2572)
- RC2/RC3 rate: standalone RC2/RC3 must run at a steady rate close to 1/5/10/20/30/40/50/100 Hz, because RaceChrono uses that rate to sync with GPS time. The count field must still be incremented for skipped updates. — [RaceChrono DIY tutorial](https://racechrono.com/article/2572)
- The tutorial warns that the BLE protocols "are very new and they may be changed (improved) in the coming releases." — [RaceChrono DIY tutorial](https://racechrono.com/article/2572)
- BLE GATT spec (GitHub aollin/racechrono-ble-diy-device):
  - Service UUID 0x1FF8. Characteristics: 0x0001 CAN main (read/notify), 0x0002 CAN filter (write), 0x0003 GPS main (read/notify), 0x0004 GPS time (read/notify), 0x0005 Monitor config (indicate/write), 0x0006 Monitor values (write without response).
  - GPS lat/lon are degrees ×10^7 as signed integers.
  - A CAN packet is a 32-bit little-endian ID plus a 1–16 byte payload. The filter supports deny-all, allow-all with a notify interval in ms, and allow-one-PID.
  - The page says the API works on both Android and iOS.
  - The "Monitor" API (0x0005/0x0006), which pushes values from the app back to the device, was added in RaceChrono v7.4.0 beta.
  - No fixed GPS rate is stated. The CAN notify interval is set per PID in ms.
  — [GitHub racechrono-ble-diy-device](https://github.com/aollin/racechrono-ble-diy-device)
- That GitHub README shows no licence, fee or usage restriction (the page I captured showed none). — [GitHub racechrono-ble-diy-device](https://github.com/aollin/racechrono-ble-diy-device)
- RaceChrono also accepts Wi-Fi NMEA GPS via RaceChrono DIY > TCP/IP > "NMEA 0183 API" (changed in v6.0). CAN channels are decoded with user-defined PIDs and "equations" in the Vehicle profile. — [RaceChrono support](https://racechrono.com/support)
- Per the RaceChrono homepage, external GPS receivers work in all versions. "DIY data sources and sensors" and Bluetooth/Wi-Fi OBD-II readers are Pro only. — [racechrono.com](https://racechrono.com/)
- Per an older Android changelog, Bluetooth GPS is limited to 10 Hz "if no Pro upgrade or Devices pack purchased (free version only)." — [RaceChrono Android changelog (search snippet)](https://racechrono.com/article/352)
- Commercial GPS rates RaceChrono supports: RaceBox Mini/Mini S at 25 Hz and Dragy Pro/DRG70 at 25 Hz. With OBDLink MX+, OBD-II can reach up to 50 Hz, shared across all logged channels. — [RaceChrono support](https://racechrono.com/support)

**Harry's LapTimer**
- On Android, any GPS implementing NMEA 0183 or later should work. LapTimer reads the NMEA stream directly. — [gps-laptimer.de Android compatibility](https://gps-laptimer.de/compatibility/android)
- The Android compatibility page lists RaceCapture (Track, Pro MK1/2/3, Apex) as integrated in LapTimer GrandPrix, preferably over Bluetooth on Android, with OBD II, CAN and analog/digital inputs at "up to 50 Hz". — [gps-laptimer.de Android compatibility](https://gps-laptimer.de/compatibility/android)
- Harry's has a "developer program" through which manufacturers and third parties add sensors; community integrations include ReDrive BLE (20 Hz GPS), RaceHF and airVentDisplay (BMW E46 CAN + GPS over BLE). The compatibility page does not document the API itself. — [gps-laptimer.de Android compatibility](https://gps-laptimer.de/compatibility/android)
- The documentation index mentions a paper that introduces the Developer Program. I could not retrieve its contents. — [LapTimer Documentation](https://gps-laptimer.de/documentation)
- On iOS, any Bluetooth GPS needs to be MFi-certified (snippet from the iOS compatibility page). — [gps-laptimer.de iOS compatibility](https://gps-laptimer.de/compatibility/ios)
- On Android it also supports custom ELM327-compatible BLE OBD adapters and DIY tyre sensors (RejsaRubberTrac, open source). — [gps-laptimer.de Android compatibility](https://gps-laptimer.de/compatibility/android)

**TrackAddict (HP Tuners)**
- External GPS: standard NMEA-0183 (RMC, GGA, GLL) over Bluetooth SPP, Android only, 1–20 Hz. The phone's internal GPS goes up to 20 Hz. — [TrackAddict documentation](https://support.hptuners.com/support/solutions/articles/153000175762-trackaddict-documentation)
- Custom devices use the Numeric Broadcast Protocol (NBP). Transports: classic Bluetooth SPP (Android only), Wi-Fi with a user-entered IP and port (iOS and Android), and USB OTG (Android, experimental). — [TrackAddict documentation](https://support.hptuners.com/support/solutions/articles/153000175762-trackaddict-documentation)
- The NBP spec v1.1.2 (2021-03-04, HP Tuners) is a public PDF, "provided as-is to promote interoperability between products." It is supported by TrackAddict v4.2+ (v4.6.4 for the latest features). These details come from search snippets; I could not open the PDF. — [NBP Specification PDF](https://racerender.com/TrackAddict/docs/NBP%20Specification.pdf)
- A third-party Python implementation exists (pynbp). — [pynbp on PyPI](https://pypi.org/project/pynbp)
- OBD data is "generally limited to the standard SAE / Mode 01 parameter set." — [TrackAddict documentation](https://support.hptuners.com/support/solutions/articles/153000175762-trackaddict-documentation)

**Garmin Catalyst 2 (closed)**
- It does not connect to a car's OBD data, and I found no external-sensor import. Data comes only from its built-in sensors. — [Ross Bentley, Another Catalyst for Change](https://rossbentley.substack.com/p/another-catalyst-for-change); [BimmerWorld](https://www.bimmerworld.com/Gauges-Data-Acquisition/Data-Acquisition-Systems/Garmin-Catalyst-2-Driving-Performance-Optimizer-Camera.html)

**Other Android apps that take external GNSS**
- LITPro pairs a RaceBox Micro or Mini S at 1–25 Hz (snippet). — [search result summary; LITPro app listing, URL not captured]
- Solostorm is aimed at autocross, hill climb, ProSolo and time attack. One forum post says its site still recommends a Samsung tablet that Samsung stopped supporting in 2019. I found no source confirming which external devices or protocols it supports. — [Grassroots/Classic Motorsports forum](https://classicmotorsports.com/forum/grm/turn-a-smartphone-into-a-data/274870/page1)

### Inferences
- Our logger already emulates the RaceCapture protocol (RCP), and Harry's LapTimer GrandPrix lists RaceCapture as a supported device. Our existing RCP emulation might therefore feed Harry's directly, live, with GPS + CAN + analog. This is unverified and needs a test. It would also keep RCP alive as a de facto interface even after leaving Podium.
- For RaceChrono, RC2/RC3 over TCP (Wi-Fi) or RFCOMM is the lowest-effort route. The UNO Q's Linux side could emit $GPRMC/$GPGGA at 10 Hz plus $RC3 (IMU + up to 15 analog/derived channels such as RPM, water temperature and SOC). BLE is better for raw CAN frames (decoded in-app by equations) but is flagged as subject to change.
- TrackAddict NBP over Wi-Fi TCP is the only documented custom-sensor protocol that also works on iOS. It carries named numeric channels, which suits pre-decoded values.
- No vendor states a licence fee for implementing these protocols. But none grants an explicit licence either, so before selling a logger it would be prudent to confirm with RaceChrono and HP Tuners (especially for marketing claims like "RaceChrono compatible").

### Gaps
- I found no explicit licence or terms of use for implementing the RaceChrono DIY or NBP protocols, and no statement on commercial devices. I could not open the NBP PDF to confirm its packet syntax or rate limits.
- The Harry's LapTimer developer-program API is not publicly documented. I don't know whether a self-built device can join without vendor involvement.
- The maximum RC2/RC3 rate RaceChrono accepts together with 10 Hz NMEA is unconfirmed (the tutorial lists up to 100 Hz). The practical channel/rate limit over the BLE CAN API is not documented.
- Garmin Catalyst 2 appears to be a closed system. No sources contradicted that.

## Post-session import formats and paid-tier requirement

### Takeaway
RaceChrono Pro is the only phone app with documented import of foreign logs. A developer recommends .vbo (needs latitude, longitude, speed and heading; custom channels are imported from .vbo since v7.5). NMEA import also exists. Both require Pro (or the older "Devices pack"). TrackAddict and Harry's document export formats but not import of third-party logs.

### Cited Findings
- A RaceChrono forum post: the old "NMEA file device" moved under the "RaceChrono DIY" device and needs the "Devices pack" or Pro. The main-screen import facility also requires Pro and imports a log "in seconds". — [RaceChrono forum: Can we still import NMEA files?](https://racechrono.com/forum/discussion/1654/can-we-still-import-nmea-files)
- The developer recommends .vbo for non-standard data because both import and export are supported. Import needs heading, speed (kph or mph), latitude and longitude. The v7.5 beta notes "custom channels imported from .VBO files" and an improved Import screen. — [RaceChrono forum (search summary)](https://racechrono.com/forum/discussion/comment/12422/)
- RaceChrono Pro exports .ODS, .NMEA, .VBO and .CSV. Export is listed as Pro only. — [racechrono.com](https://racechrono.com/); [App Store listing](https://apps.apple.com/us/app/racechrono-pro/id1129429340)
- The RaceChrono main screen can also import GoPro video files and extract their GPS location data. — [RaceChrono support](https://racechrono.com/support)
- TrackAddict exports interpolated CSV, GPX, KML and VBO, and shares to RaceRender. Its docs do not mention import. — [TrackAddict documentation](https://support.hptuners.com/support/solutions/articles/153000175762-trackaddict-documentation)
- The Harry's Android compatibility page does not list data-import formats. — [gps-laptimer.de Android compatibility](https://gps-laptimer.de/compatibility/android)

### Inferences
- The most practical "after the session, on a phone" route is for the logger to write a .vbo file (Racelogic text format) with GPS + CAN + IMU channels and import it into RaceChrono Pro on the Pixel. The same .vbo also opens in Racelogic Circuit Tools on Windows (free), so one export format serves both phone and PC.
- Alternatively, record a session in RaceChrono while the logger streams live (RC2/RC3 or BLE). That avoids import entirely, and the phone gets video overlay too.

### Gaps
- There is no official, current RaceChrono help page for the Android import steps. The forum posts are from the v7.x era, while the current version is v10.3.3.
- Whether TrackAddict or Harry's can import .vbo or CSV from a third-party logger: no source found.

## Analysis features on phone (overlay, delta, track map, video)

### Takeaway
RaceChrono Pro provides synchronised graph, map and video analysis, a predictive lap timer, a time-delta graph, multi-camera video and video export with overlay on Android and iOS. The free Android RaceChrono has graph and map only. Harry's and TrackAddict also do video overlay. Catalyst does on-device coaching but is closed.

### Cited Findings
- RaceChrono Pro only: predictive lap timing and time-delta graph; hardware-accelerated video export with data overlay; multi-camera and picture-in-picture; GoPro remote control. Both versions: lap timing with sectors and optimal lap, 2,000+ tracks, custom circuits, unlimited session length. The free Android version has "synchronised graph and map analysis" but no video. — [racechrono.com](https://racechrono.com/)
- Harry's LapTimer overlays footage from any external H.264 HD or Full HD action camera. Automatic GoPro HERO3/3+ recording requires GrandPrix. — [gps-laptimer.de Android compatibility](https://gps-laptimer.de/compatibility/android)
- TrackAddict mentions a "Live Telemetry Streaming feature" that needs internet access, with no further detail in its docs. — [TrackAddict documentation](https://support.hptuners.com/support/solutions/articles/153000175762-trackaddict-documentation)
- Garmin Catalyst 2 overlays video with GPS data but not OBD data. — [BimmerWorld](https://www.bimmerworld.com/Gauges-Data-Acquisition/Data-Acquisition-Systems/Garmin-Catalyst-2-Driving-Performance-Optimizer-Camera.html)

### Inferences
- For an in-car driver display, RaceChrono's live delta plus the BLE "Monitor" API (which pushes values back to the device) could let the logger's own display or LEDs show RaceChrono's predictive delta. This would need a test.

### Gaps
- I did not verify a feature-by-feature comparison for Harry's editions (Rookie, Petrolhead, GrandPrix) or for TrackAddict free vs Pro.
- I did not check what TrackAddict's live telemetry streaming offers, where it goes, or what it costs.

## Cost, platforms, maintenance status

### Takeaway
RaceChrono is actively maintained: v10.3.3 for Android and iOS was released 13 Nov 2026. I could not confirm current prices for RaceChrono Pro, Harry's or TrackAddict Pro from primary sources. Garmin Catalyst 2 costs USD 1,199.99.

### Cited Findings
- RaceChrono Pro v10.3.3 (iOS) and RaceChrono v10.3.3 (Android), both dated 13.11.2026. RaceChrono Pro runs on iOS and Android; the basic RaceChrono is Android only. — [racechrono.com](https://racechrono.com/)
- Harry's LapTimer is on iOS and Android, with a recent requirement of "LapTimer v24.6.2 or later" for RaceBox. Prices not captured. — [gps-laptimer.de Android compatibility](https://gps-laptimer.de/compatibility/android)
- TrackAddict runs on iOS and Android; the docs footer reads "© HP Tuners 2024". — [TrackAddict documentation](https://support.hptuners.com/support/solutions/articles/153000175762-trackaddict-documentation)
- Garmin Catalyst 2: suggested retail USD 1,199.99, available from 20 Feb 2026; AUD 1,999. — [rallies.ai news](https://rallies.ai/news/garmin-launches-119999-catalyst-2-motorsports-performance-optimizer-with-true-optimal-lap); [Garmin AU blog](https://www.garmin.com/en-AU/blog/?p=4181)
- The RaceBox Micro DIY kit was listed at USD 119 (pre-order) at one retailer. — [Wrekd](https://wrekd.com/products/racebox-micro-25hz-gps-diy-kit-standalone-vehicle-performance-tracker-high-precision-accelerometer-gyroscope)

### Gaps
- Current prices for RaceChrono Pro, the Devices pack, Harry's editions and TrackAddict Pro are unverified. Neither the RaceChrono site nor the docs I fetched list prices; check the Google Play listing.
- Release dates for Harry's, TrackAddict and Solostorm are unverified.

## Licence terms for third-party / self-built device data

### Takeaway
None of the vendor pages I checked state licence terms or fees for feeding self-built devices. RaceChrono and TrackAddict publish their protocols openly, and the NBP PDF says it is "provided as-is to promote interoperability". RaceChrono gates DIY input behind Pro (a user-side purchase), not a developer licence.

### Cited Findings
- NBP is "provided as-is to promote interoperability between products" (snippet). — [NBP Specification PDF](https://racerender.com/TrackAddict/docs/NBP%20Specification.pdf)
- The RaceChrono BLE DIY repo shows no licence or terms in its README. — [GitHub racechrono-ble-diy-device](https://github.com/aollin/racechrono-ble-diy-device)
- "DIY data sources and sensors" is a Pro-only feature. — [racechrono.com](https://racechrono.com/)

### Inferences
- If the logger is sold, each end user would need RaceChrono Pro (a modest one-off app purchase, price unverified) to use the DIY input. There is no evidence of a per-device licence for the logger maker. Trademark use of "RaceChrono" in marketing is a separate question.

### Gaps
- There is no explicit written permission or licence for commercial devices implementing RaceChrono DIY or NBP. Asking the developers directly is recommended.

## Open-source / self-hostable real-time telemetry viewers

### Takeaway
PlotJuggler (MPL-2.0) is the strongest open-source desktop viewer for live streams: it takes UDP, WebSocket, MQTT or ZeroMQ input with JSON, CBOR, MessagePack or Protobuf, and runs on Windows and Linux. It has no GPS map and no Android version. Foxglove went closed-source in 2024; its open fork is Lichtblick (MPL-2.0). For pit pages, the common student-team pattern is CAN to MQTT over LTE to Grafana, which matches our current architecture. I found no mature, turnkey open-source "race car + LTE + lap timing" kit.

### Cited Findings
- PlotJuggler: MPL-2.0 licence. Streaming sources: ROS 2, MQTT, ZeroMQ, UDP, WebSocket bridges, WebRTC, Lab Streaming Layer. Formats: JSON, CBOR, MessagePack, Protobuf. File import: CSV, MCAP, Parquet, ULog, MP4 and others. Builds: a Windows x64 installer that needs no admin rights, Debian/Ubuntu apt or .deb, AppImage. macOS and Android are not mentioned, and there is no GPS/map plugin listed. — [GitHub PlotJuggler](https://github.com/facontidavide/PlotJuggler)
- Foxglove announced in March 2024 that it would stop developing the open-source edition of Studio; the 1.x source remains, and future development is closed. — [Open Robotics Discourse: Foxglove 2.0](https://discourse.openrobotics.org/t/foxglove-2-0-integrated-ui-new-pricing-and-open-source-changes/36583)
- Lichtblick is a fork of Foxglove Studio under MPL-2.0. A third-party README says it is maintained by BMW. A source also describes it as "open core" with a CLA for contributors; this may come from inherited text and is unverified. — [awesome.ecosyste.ms Lichtblick](https://awesome.ecosyste.ms/projects/github.com%2Flichtblick-suite%2Flichtblick); [GitHub fork nitrobotics-dev/lichtblick](https://github.com/nitrobotics-dev/lichtblick)
- UCSolarCarTeam/Telemetry-Visualizer: a Grafana dashboard fed by MQTT, set up with Docker. — [Telemetry-Visualizer mirror](https://gh.r-mj.com/UCSolarCarTeam/Telemetry-Visualizer)
- Student-team examples of CAN to MQTT over LTE to a dashboard: Gaucho Racing added an LTE node that sends all CAN data to an MQTT broker; a solar car team used a CAN logger with GNSS and LTE upload to Grafana. — [SingleStore blog](https://www.singlestore.com/blog/building-a-real-time-analytics-pipeline-for-race-cars/); [CSS Electronics case study](https://www.csselectronics.com/pages/real-time-dashboard-telematics-solar-car)
- djhedges/exit_speed is a Raspberry Pi race logger with Grafana, streaming roughly 3–10 points per second over a phone tether. — [Grassroots Motorsports forum](https://grassrootsmotorsports.com/forum/grm/exit-speed/177062/page1)

### Inferences
- Our existing LTE to home server to Grafana/pit web pipeline is already the typical open-source pattern. PlotJuggler could be added cheaply as a Windows engineer's live view by having the server republish values over MQTT or WebSocket JSON. It is not a phone tool.
- On Android, live in-car or pit use would come from RaceChrono (in-car, via the DIY protocol) plus our own web pages for the pit. No open-source Android lap-timing app with a documented external-device protocol turned up.

### Gaps
- Grafana Live (streaming push) was not researched with primary sources in this pass. Its capabilities and limits are not verified here.
- I did not find the latest PlotJuggler release version or date (the Releases section did not render).
- I did not find mature open-source Android lap timers that accept external devices; the searches returned none.
