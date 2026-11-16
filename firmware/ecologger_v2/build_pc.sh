#!/bin/sh
# PC（Windows の Git Bash）で、本体の build.sh と同じ手順で組んで大きさを測る（2026-11-17、SP-7-8）。書き込みはしない。
#   sh build_pc.sh <ソースのフォルダ> <出力のフォルダ>
# 用意（README の「PCで組む」）：$ARDUINO_UNOQ（無ければ ~/arduino-unoq）に arduino-cli 1.4.0 と arduino:zephyr@0.52.0、
# 本体の控えから写した ecologger_v2_libraries（unoq_ref/ の下）と、本体の build.sh が手直しした5つのライブラリのファイル
set -eu
HERE=${ARDUINO_UNOQ:-$HOME/arduino-unoq}
SRC=$1; OUT=$2
T=$HERE/data/packages/zephyr/tools/arm-zephyr-eabi/0.16.8/bin/arm-zephyr-eabi-
rm -rf "$OUT"; mkdir -p "$OUT/sketch/ecologger_v2"
cp "$SRC"/*.ino "$SRC"/*.h "$OUT/sketch/ecologger_v2/"
"$HERE/bin/arduino-cli.exe" --config-file "$HERE/arduino-cli.yaml" compile -b arduino:zephyr:unoq --libraries "$HERE/unoq_ref/ecologger_v2_libraries" --output-dir "$OUT/build" "$OUT/sketch/ecologger_v2" > "$OUT/compile.log" 2>&1 || { tail -30 "$OUT/compile.log"; exit 1; }
B=$OUT/build
"${T}objcopy" -G setup -G loop "$B/ecologger_v2.ino.elf" "$B/logger_compact.elf"
"${T}strip" --strip-unneeded "$B/logger_compact.elf"
python "$SRC/compact_symbols.py" "$T" "$B/logger_compact.elf" "$B/logger_short.elf"
mv "$B/logger_short.elf" "$B/logger_compact.elf"
"$HERE/data/packages/arduino/tools/zephyr-sketch-tool/0.2.0/zephyr-sketch-tool.exe" "$B/logger_compact.elf" > "$OUT/zsk.log" 2>&1 || { cat "$OUT/zsk.log"; exit 1; }
python "$SRC/audit_image.py" "$B/logger_compact.elf-zsk.bin" --output "$B/image-audit.json"
wc -c < "$B/logger_compact.elf-zsk.bin"; sha256sum "$B/logger_compact.elf-zsk.bin" | cut -c1-16; cat "$B/image-audit.json"
