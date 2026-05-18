#!/usr/bin/env bash
# hwp2x.sh — convert HWP/HWPX to PDF or DOCX via LibreOffice + H2Orestart (headless).
# Usage: hwp2x.sh <pdf|docx> <input.hwp[x]> [<outdir>]
# Outputs <outdir>/<basename>.<fmt> (defaults to alongside input).

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <pdf|docx> <input.hwp[x]> [<outdir>]" >&2
  exit 2
fi

fmt=$1
input=$2
outdir=${3:-$(dirname "$input")}

case "$fmt" in
  pdf|docx) ;;
  *) echo "error: unsupported format '$fmt' (expected pdf or docx)" >&2; exit 2 ;;
esac

export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$PATH"

SOFFICE=/Applications/LibreOffice.app/Contents/MacOS/soffice

# .hwp (binary HWP5) needs explicit filter; .hwpx is auto-detected.
ext_lower=$(printf '%s' "${input##*.}" | tr '[:upper:]' '[:lower:]')
filter_args=()
if [[ $ext_lower == "hwp" ]]; then
  filter_args=(--infilter='Hwp2002_File')
fi

"$SOFFICE" \
  --headless \
  --norestore --nologo --nofirststartwizard \
  ${filter_args[@]+"${filter_args[@]}"} \
  --convert-to "$fmt" \
  --outdir "$outdir" \
  "$input"
