# Minimal usage
# From repo root:
# run this first once to make the script executable:
# chmod +x scripts/make_srcset_images.sh

# call the script with two optional arguments:
# ./scripts/make_srcset_images.sh "/in" "/out" [jobs] [--dry-run]
#
# to set jobs only (keep default folders), use the env var:
# MAKE_SRCSET_JOBS=6 ./scripts/make_srcset_images.sh
#
# optional: generate 2400px primaries only for selected work IDs:
# MAKE_SRCSET_2400_IDS_FILE=./data/srcset_2400_ids.txt ./scripts/make_srcset_images.sh
# file format: one work_id per line (exact match), e.g.:
#   00361
#   00405
#
# optional: process only selected work IDs:
# MAKE_SRCSET_WORK_IDS_FILE=./tmp/work_ids.txt ./scripts/make_srcset_images.sh
# file format: one work_id per line (exact match).
#
# optional: write successfully processed work IDs (one per line):
# MAKE_SRCSET_SUCCESS_IDS_FILE=./tmp/srcset_success_ids.txt ./scripts/make_srcset_images.sh

#!/usr/bin/env bash
set -euo pipefail

# ---------
# CONFIG
# ---------
DRY_RUN=0
POSITIONAL=()
for arg in "$@"; do
  case "$arg" in
    --dry-run)
      DRY_RUN=1
      ;;
    *)
      POSITIONAL+=("$arg")
      ;;
  esac
done
set -- "${POSITIONAL[@]}"

BASE_DIR="/Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform"
INPUT_DIR="${1:-$BASE_DIR/works/make_srcset_images}" # where {work_id}.jpg lives
OUTPUT_DIR="${2:-$BASE_DIR/works/srcset_images}"     # base output folder for derivative subfolders
JOBS="${3:-${MAKE_SRCSET_JOBS:-1}}" # number of parallel jobs (default 1 = serial)
INCLUDE_2400_IDS_FILE="${MAKE_SRCSET_2400_IDS_FILE:-}"
WORK_IDS_FILE="${MAKE_SRCSET_WORK_IDS_FILE:-}"
SUCCESS_IDS_FILE="${MAKE_SRCSET_SUCCESS_IDS_FILE:-}"
REPORT_FILE="$(mktemp -t make_srcset_report.XXXXXX)"
PROCESSED_SOURCES_FILE="$(mktemp -t make_srcset_processed_sources.XXXXXX)"

# Quality settings (tune if needed)
WEBP_PRESET="photo"
PRIMARY_Q=82
THUMB_Q=78
COMPRESSION_LEVEL=6

if [[ "$DRY_RUN" -eq 0 ]]; then
  mkdir -p "$OUTPUT_DIR/primary"
  mkdir -p "$OUTPUT_DIR/thumb"
fi

# Check ffmpeg exists
command -v ffmpeg >/dev/null 2>&1 || {
  echo "Error: ffmpeg not found. Install ffmpeg first."
  exit 1
}

# Check optional converters for HEIC/HEIF
HAS_SIPS=0
HAS_HEIF_CONVERT=0
if command -v sips >/dev/null 2>&1; then
  HAS_SIPS=1
fi
if command -v heif-convert >/dev/null 2>&1; then
  HAS_HEIF_CONVERT=1
fi

# ---------
# HELPERS
# ---------
make_thumb() {
  local in="$1"
  local size="$2"
  local out="$3"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY-RUN write thumb: $out"
    printf 'thumb|dry|%s\n' "$out" >> "$REPORT_FILE"
    return 0
  fi

  # Centre-crop square thumbnail:
  # 1) scale so the *shorter* dimension becomes the target size
  # 2) crop target x target from the centre
  ffmpeg -hide_banner -loglevel error -y \
    -i "$in" \
    -map_metadata -1 \
    -vf "scale='if(gt(iw,ih),-1,${size})':'if(gt(iw,ih),${size},-1)':flags=lanczos,crop=${size}:${size}" \
    -c:v libwebp -preset "$WEBP_PRESET" -q:v "$THUMB_Q" -compression_level "$COMPRESSION_LEVEL" \
    "$out"
  echo "Wrote thumb: $out"
  printf 'thumb|written|%s\n' "$out" >> "$REPORT_FILE"
}

make_primary() {
  local in="$1"
  local width="$2"
  local out="$3"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY-RUN write primary-${width}: $out"
    printf 'primary-%s|dry|%s\n' "$width" "$out" >> "$REPORT_FILE"
    return 0
  fi

  # Resize to target width, preserve aspect ratio, and do NOT upscale
  ffmpeg -hide_banner -loglevel error -y \
    -i "$in" \
    -map_metadata -1 \
    -vf "scale=w='min(iw,${width})':h=-2:flags=lanczos" \
    -c:v libwebp -preset "$WEBP_PRESET" -q:v "$PRIMARY_Q" -compression_level "$COMPRESSION_LEVEL" \
    "$out"
  echo "Wrote primary-${width}: $out"
  printf 'primary-%s|written|%s\n' "$width" "$out" >> "$REPORT_FILE"
}

should_make_2400() {
  local work_id="$1"
  if [[ -z "$INCLUDE_2400_IDS_FILE" ]]; then
    return 0
  fi
  grep -Fxq "$work_id" "$INCLUDE_2400_IDS_FILE"
}

should_process_work_id() {
  local work_id="$1"
  if [[ -z "$WORK_IDS_FILE" ]]; then
    return 0
  fi
  grep -Fxq "$work_id" "$WORK_IDS_FILE"
}

record_success_id() {
  local work_id="$1"
  if [[ "$DRY_RUN" -eq 0 && -n "$SUCCESS_IDS_FILE" ]]; then
    printf '%s\n' "$work_id" >> "$SUCCESS_IDS_FILE"
  fi
}

record_processed_source() {
  local src="$1"
  printf '%s\n' "$src" >> "$PROCESSED_SOURCES_FILE"
}

process_one() {
  local src="$1"
  local fname work_id src_use ext ext_lc tmp_dir tmp_jpg

  fname="$(basename "$src")"
  work_id="${fname%.*}"  # {work_id} from {work_id}.ext

  if ! should_process_work_id "$work_id"; then
    echo "Skipping $fname (work_id not listed in MAKE_SRCSET_WORK_IDS_FILE)"
    return 0
  fi

  # Use original source by default; for HEIC/HEIF we convert first due to FFmpeg limitations
  src_use="$src"
  ext="${fname##*.}"
  # macOS ships Bash 3.2 by default; avoid Bash 4 `${var,,}`
  ext_lc="$(printf '%s' "$ext" | tr '[:upper:]' '[:lower:]')"

  if [[ "$ext_lc" == "heic" || "$ext_lc" == "heif" ]]; then
    tmp_dir="$(mktemp -d 2>/dev/null || mktemp -d -t dlf_heic)"
    tmp_jpg="$tmp_dir/${work_id}.jpg"
    if [[ "$HAS_SIPS" -eq 1 ]]; then
      echo "Converting $fname -> $(basename "$tmp_jpg") (sips)"
      sips -s format jpeg -s formatOptions 90 "$src" --out "$tmp_jpg" >/dev/null
      src_use="$tmp_jpg"
    elif [[ "$HAS_HEIF_CONVERT" -eq 1 ]]; then
      echo "Converting $fname -> $(basename "$tmp_jpg") (heif-convert)"
      heif-convert -q 90 "$src" "$tmp_jpg" >/dev/null
      src_use="$tmp_jpg"
    else
      echo "Warning: $fname is HEIC/HEIF but neither 'sips' nor 'heif-convert' is available. Skipping."
      rm -rf "$tmp_dir"
      return 0
    fi
  fi

  echo "Processing $fname -> $work_id"

  make_thumb  "$src_use" 96  "$OUTPUT_DIR/thumb/${work_id}-thumb-96.webp"
  make_thumb  "$src_use" 192 "$OUTPUT_DIR/thumb/${work_id}-thumb-192.webp"
  make_primary "$src_use" 800  "$OUTPUT_DIR/primary/${work_id}-primary-800.webp"
  make_primary "$src_use" 1200 "$OUTPUT_DIR/primary/${work_id}-primary-1200.webp"
  make_primary "$src_use" 1600 "$OUTPUT_DIR/primary/${work_id}-primary-1600.webp"
  if should_make_2400 "$work_id"; then
    make_primary "$src_use" 2400 "$OUTPUT_DIR/primary/${work_id}-primary-2400.webp"
  else
    echo "Skipping 2400px primary for $work_id (not listed in MAKE_SRCSET_2400_IDS_FILE)"
  fi
  record_success_id "$work_id"
  record_processed_source "$src"

  if [[ -n "${tmp_dir:-}" && -d "${tmp_dir:-}" ]]; then
    rm -rf "$tmp_dir"
  fi
}

# ---------
# RUN
# ---------
shopt -s nullglob
found=0

# Collect sources
sources=(
  "$INPUT_DIR"/*.jpg "$INPUT_DIR"/*.JPG
  "$INPUT_DIR"/*.jpeg "$INPUT_DIR"/*.JPEG
  "$INPUT_DIR"/*.heic "$INPUT_DIR"/*.HEIC
  "$INPUT_DIR"/*.heif "$INPUT_DIR"/*.HEIF
  "$INPUT_DIR"/*.png "$INPUT_DIR"/*.PNG
  "$INPUT_DIR"/*.tif "$INPUT_DIR"/*.TIF
  "$INPUT_DIR"/*.tiff "$INPUT_DIR"/*.TIFF
)

if [[ ${#sources[@]} -gt 0 ]]; then
  found=1
fi

if [[ "$found" -eq 1 ]]; then
  if [[ -n "$INCLUDE_2400_IDS_FILE" && ! -f "$INCLUDE_2400_IDS_FILE" ]]; then
    echo "Error: MAKE_SRCSET_2400_IDS_FILE not found: $INCLUDE_2400_IDS_FILE"
    exit 1
  fi
  if [[ -n "$WORK_IDS_FILE" && ! -f "$WORK_IDS_FILE" ]]; then
    echo "Error: MAKE_SRCSET_WORK_IDS_FILE not found: $WORK_IDS_FILE"
    exit 1
  fi
  if [[ -n "$SUCCESS_IDS_FILE" ]]; then
    mkdir -p "$(dirname "$SUCCESS_IDS_FILE")"
    : > "$SUCCESS_IDS_FILE"
  fi
  if [[ "$JOBS" -le 1 ]]; then
    for src in "${sources[@]}"; do
      process_one "$src"
    done
  else
    # Parallel: one source per job
    export -f process_one make_thumb make_primary should_make_2400 should_process_work_id record_success_id record_processed_source
    export OUTPUT_DIR WEBP_PRESET PRIMARY_Q THUMB_Q COMPRESSION_LEVEL HAS_SIPS HAS_HEIF_CONVERT INCLUDE_2400_IDS_FILE WORK_IDS_FILE SUCCESS_IDS_FILE DRY_RUN REPORT_FILE PROCESSED_SOURCES_FILE
    printf '%s\0' "${sources[@]}" | xargs -0 -n 1 -P "$JOBS" bash -c '
      process_one "$1"
    ' _
  fi
fi

if [[ "$found" -eq 0 ]]; then
  echo "No supported image files found in: $INPUT_DIR (jpg/jpeg/heic/heif/png/tif/tiff)"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "Dry-run: no source images found; skipping derivative simulation."
    exit 0
  fi
  exit 1
fi

# Cleanup only the sources successfully processed in this run.
processed_count="$(wc -l < "$PROCESSED_SOURCES_FILE" | tr -d ' ')"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "DRY-RUN delete source file(s): $processed_count from: $INPUT_DIR"
else
  if [[ "$processed_count" -gt 0 ]]; then
    while IFS= read -r src_path; do
      [[ -n "$src_path" ]] || continue
      rm -f -- "$src_path"
    done < "$PROCESSED_SOURCES_FILE"
  fi
  echo "Deleted $processed_count source file(s) from: $INPUT_DIR"
fi

echo "Done. Primaries written to: $OUTPUT_DIR/primary"
echo "Done. Thumbnails written to: $OUTPUT_DIR/thumb"

# Derivative summary report
written_total="$(awk -F'|' '$2=="written"{c++} END{print c+0}' "$REPORT_FILE")"
dry_total="$(awk -F'|' '$2=="dry"{c++} END{print c+0}' "$REPORT_FILE")"
written_p800="$(awk -F'|' '$1=="primary-800" && $2=="written"{c++} END{print c+0}' "$REPORT_FILE")"
written_p1200="$(awk -F'|' '$1=="primary-1200" && $2=="written"{c++} END{print c+0}' "$REPORT_FILE")"
written_p1600="$(awk -F'|' '$1=="primary-1600" && $2=="written"{c++} END{print c+0}' "$REPORT_FILE")"
written_p2400="$(awk -F'|' '$1=="primary-2400" && $2=="written"{c++} END{print c+0}' "$REPORT_FILE")"
written_thumbs="$(awk -F'|' '$1=="thumb" && $2=="written"{c++} END{print c+0}' "$REPORT_FILE")"
dry_p800="$(awk -F'|' '$1=="primary-800" && $2=="dry"{c++} END{print c+0}' "$REPORT_FILE")"
dry_p1200="$(awk -F'|' '$1=="primary-1200" && $2=="dry"{c++} END{print c+0}' "$REPORT_FILE")"
dry_p1600="$(awk -F'|' '$1=="primary-1600" && $2=="dry"{c++} END{print c+0}' "$REPORT_FILE")"
dry_p2400="$(awk -F'|' '$1=="primary-2400" && $2=="dry"{c++} END{print c+0}' "$REPORT_FILE")"
dry_thumbs="$(awk -F'|' '$1=="thumb" && $2=="dry"{c++} END{print c+0}' "$REPORT_FILE")"

echo "Derivative report:"
echo "  written total: $written_total (thumb=$written_thumbs, p800=$written_p800, p1200=$written_p1200, p1600=$written_p1600, p2400=$written_p2400)"
echo "  dry-run total: $dry_total (thumb=$dry_thumbs, p800=$dry_p800, p1200=$dry_p1200, p1600=$dry_p1600, p2400=$dry_p2400)"

rm -f "$REPORT_FILE"
rm -f "$PROCESSED_SOURCES_FILE"
