#!/usr/bin/env bash
# Pinned toolchain for every render job: ffmpeg 7.0.2 static (same binary as the planning sandbox), Montserrat, FSRCNN x4.
set -euo pipefail
T="${RUNNER_TEMP:-/tmp}/wwb-tools"; mkdir -p "$T/bin" "$T/fonts" "$T/models"
if [ ! -x "$T/bin/ffmpeg" ]; then
  curl -fsSL --retry 5 -o "$T/ff.tar.xz" https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
  echo "7fa72b652e19bf84c9461e332ea1cdf3  $T/ff.tar.xz" | md5sum -c -
  tar -xJf "$T/ff.tar.xz" -C "$T" && cp "$T"/ffmpeg-*-static/ffmpeg "$T"/ffmpeg-*-static/ffprobe "$T/bin/"
fi
echo "e7e7fb30477f717e6f55f9180a70386c62677ef8a4d4d1a5d948f4098aa3eb99  $T/bin/ffmpeg" | sha256sum -c -
echo "4f231a1960d83e403d08f7971e271707bec278a9ae18e21b8b5b03186668450d  $T/bin/ffprobe" | sha256sum -c -
for f in Black:ea67b37f8776eebea135cd1fe9adeaf6f9427683e8dc11ab8398b6be5f102c60 Bold:bc6e854971cea46b463be6f9eef4d9cd52f51cfc1fc0dd90c9d3e6483dc0ec61 ExtraBold:d3ac6a843d3ba6d5cafd44cf39e437055c8aed7e261010f595f57d3c7b3e2c1b SemiBold:b4e1563393d73fdff491a869441245aef31add2ec03d9c97a6dae4de07c52fd0; do
  n=${f%%:*}; h=${f##*:}; p="$T/fonts/Montserrat-$n.ttf"
  [ -f "$p" ] || curl -fsSL --retry 5 -o "$p" "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-$n.ttf"
  echo "$h  $p" | sha256sum -c -
done
p="$T/models/FSRCNN_x4.pb"; [ -f "$p" ] || curl -fsSL --retry 5 -o "$p" https://raw.githubusercontent.com/Saafke/FSRCNN_Tensorflow/master/models/FSRCNN_x4.pb
echo "5c68d18db561aed8ead4ffedf1b897ea615baaf60ebf6c35f8e641f8fa4a21bf  $p" | sha256sum -c -
mkdir -p ~/.fonts && cp "$T"/fonts/*.ttf ~/.fonts/ && (fc-cache -f >/dev/null 2>&1 || true)
{ echo "$T/bin"; } >> "${GITHUB_PATH:-/dev/null}"
{ echo "WWB_FONTS=$T/fonts"; echo "FSRCNN_MODEL=$p"; } >> "${GITHUB_ENV:-/dev/null}"
export PATH="$T/bin:$PATH"; ffmpeg -version | head -1
