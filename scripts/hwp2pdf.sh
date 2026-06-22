#!/usr/bin/env bash
# hwp2pdf.sh — render HWP/HWPX to PDF via rhwp (single self-contained binary,
# no Java / no LibreOffice). Handles both binary .hwp (HWP5) and .hwpx natively.
# Usage: hwp2pdf.sh <input.hwp[x]> [<outdir>]
# Writes <outdir>/<basename>.pdf (outdir defaults to alongside input).

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <input.hwp[x]> [<outdir>]" >&2
  exit 2
fi

input=$1
outdir=${2:-$(dirname "$input")}

repo_root=$(cd "$(dirname "$0")/.." && pwd)

# Locate the rhwp binary: explicit override → repo-vendored → PATH.
if [[ -n "${RHWP_BIN:-}" ]]; then
  rhwp=$RHWP_BIN
elif [[ -x "$repo_root/vendor/rhwp/rhwp" ]]; then
  rhwp="$repo_root/vendor/rhwp/rhwp"
elif command -v rhwp >/dev/null 2>&1; then
  rhwp=$(command -v rhwp)
else
  echo "error: rhwp binary not found. Run scripts/fetch_rhwp.sh first." >&2
  exit 3
fi

base=$(basename "$input")
out="$outdir/${base%.*}.pdf"

# RHWP_FONT_PATH (optional, ':'-separated) lets a server without the document's
# fonts point rhwp at a font directory; on macOS the system fonts suffice.
font_args=()
if [[ -n "${RHWP_FONT_PATH:-}" ]]; then
  IFS=':' read -ra _paths <<< "$RHWP_FONT_PATH"
  for p in "${_paths[@]}"; do
    [[ -n "$p" ]] && font_args+=(--font-path "$p")
  done
fi

exec "$rhwp" export-pdf "$input" -o "$out" ${font_args[@]+"${font_args[@]}"}
