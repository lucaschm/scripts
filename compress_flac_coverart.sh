#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/music/folder"
  exit 1
fi

ROOT="$1"

if [[ ! -d "$ROOT" ]]; then
  echo "Error: '$ROOT' is not a directory"
  exit 1
fi

echo "Processing FLAC files under: $ROOT"
echo "Cover art target: JPEG, max 800x800, quality 85"
echo

find "$ROOT" -type f -iname "*.flac" | while read -r FLAC; do
  echo "→ $FLAC"

  TMPDIR=$(mktemp -d)
  SRC_IMG="$TMPDIR/cover"
  OUT_IMG="$TMPDIR/cover_800.jpg"

  # Extract embedded cover art
  if ! metaflac --export-picture-to="$SRC_IMG" "$FLAC" 2>/dev/null; then
    echo "  No embedded cover art, skipping"
    rm -rf "$TMPDIR"
    continue
  fi

  EXT=$(file --extension "$SRC_IMG" | cut -d/ -f1)
  SRC_IMG_EXT="$SRC_IMG.$EXT"
  mv "$SRC_IMG" "$SRC_IMG_EXT"

  # Resize & recompress (never upscale)
  convert "$SRC_IMG_EXT" \
    -resize 800x800\> \
    -strip \
    -sampling-factor 4:2:0 \
    -quality 90 \
    "$OUT_IMG"

  # Remove ALL existing artwork (portable, reliable)
  metaflac --remove --block-type=PICTURE "$FLAC"

  # Embed resized artwork
  metaflac --import-picture-from="$OUT_IMG" "$FLAC"

  rm -rf "$TMPDIR"
done

echo
echo "Done."
