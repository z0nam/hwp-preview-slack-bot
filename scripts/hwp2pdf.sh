#!/usr/bin/env bash
# hwp2pdf.sh — convert HWP/HWPX to PDF via LibreOffice + H2Orestart (headless).
# Usage: hwp2pdf.sh <input.hwp[x]> [<outdir>]
# Outputs <outdir>/<basename>.pdf (defaults to alongside input).

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <input.hwp[x]> [<outdir>]" >&2
  exit 2
fi

input=$1
outdir=${2:-$(dirname "$input")}

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
  --convert-to pdf \
  --outdir "$outdir" \
  "$input"
