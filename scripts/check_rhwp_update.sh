#!/usr/bin/env bash
# check_rhwp_update.sh — check whether a newer rhwp release exists and, if so,
# smoke-test the new binary on the bundled samples BEFORE adopting it. The
# live vendor/rhwp/rhwp is only replaced when the candidate converts both
# samples cleanly; a regressed release is reported and discarded.
#
# Usage:
#   scripts/check_rhwp_update.sh            check; apply iff the candidate passes
#   scripts/check_rhwp_update.sh --dry-run  check + smoke-test, never modify anything
#
# Testing the "new version found" path while already on the latest tag:
#   RHWP_PIN_OVERRIDE=v0.7.10 scripts/check_rhwp_update.sh --dry-run
#
# Exit codes: 0 = up to date OR updated/would-update OK; 1 = candidate failed
# smoke test; 2 = usage/lookup error. Requires gh, tar, shasum.
set -euo pipefail

RHWP_REPO="edwardkim/rhwp"
repo_root=$(cd "$(dirname "$0")/.." && pwd)
fetch_script="$repo_root/scripts/fetch_rhwp.sh"
dest_dir="$repo_root/vendor/rhwp"

dry_run=0
[[ "${1:-}" == "--dry-run" ]] && dry_run=1

# Current pinned version (RHWP_PIN_OVERRIDE lets tests pretend an older pin).
pinned=${RHWP_PIN_OVERRIDE:-$(awk -F'"' '/^RHWP_VERSION=/{print $2}' "$fetch_script")}
[[ -n "$pinned" ]] || { echo "error: could not read RHWP_VERSION from $fetch_script" >&2; exit 2; }

latest=$(gh api "repos/$RHWP_REPO/releases/latest" --jq .tag_name 2>/dev/null || true)
[[ -n "$latest" ]] || { echo "error: could not query latest release for $RHWP_REPO" >&2; exit 2; }

echo "pinned: $pinned   latest: $latest"
if [[ "$pinned" == "$latest" ]]; then
  echo "✓ already on the latest rhwp ($latest). Nothing to do."
  exit 0
fi
echo "→ newer release available: $latest"

# Map uname → release asset slug (mirror of fetch_rhwp.sh).
os=$(uname -s); arch=$(uname -m)
case "$os/$arch" in
  Darwin/arm64)  slug="macos-aarch64" ;;
  Darwin/x86_64) slug="macos-x86_64" ;;
  Linux/x86_64)  slug="linux-x86_64" ;;
  *) echo "error: no prebuilt rhwp for $os/$arch" >&2; exit 2 ;;
esac
asset="rhwp-$latest-$slug.tar.gz"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

echo "Downloading candidate ${asset}…"
gh release download "$latest" --repo "$RHWP_REPO" \
  --pattern "$asset" --pattern "SHA256SUMS.txt" --dir "$tmp" --clobber

want=$(awk -v a="$asset" '$2==a{print $1}' "$tmp/SHA256SUMS.txt")
got=$(shasum -a 256 "$tmp/$asset" | awk '{print $1}')
if [[ -z "$want" || "$want" != "$got" ]]; then
  echo "✗ checksum mismatch for $asset (want=$want got=$got) — discarding candidate." >&2
  exit 1
fi
echo "  checksum ok: $got"

tar xzf "$tmp/$asset" -C "$tmp"
cand="$tmp/rhwp/rhwp"
chmod +x "$cand"
xattr -d com.apple.quarantine "$cand" 2>/dev/null || true

# Smoke test: convert each bundled sample with the candidate binary and require
# a non-trivial PDF out. (pdfinfo, if present, additionally asserts pages > 0.)
echo "Smoke-testing candidate on samples/…"
ok=1
tested=0
for s in "$repo_root"/samples/sample-binary.hwp "$repo_root"/samples/sample-xml.hwpx; do
  [[ -f "$s" ]] || continue
  tested=$((tested + 1))
  out="$tmp/$(basename "${s%.*}").pdf"
  if ! "$cand" export-pdf "$s" -o "$out" >/dev/null 2>&1; then
    echo "  ✗ $(basename "$s"): conversion exited non-zero"; ok=0; continue
  fi
  size=$(stat -f%z "$out" 2>/dev/null || stat -c%s "$out" 2>/dev/null || echo 0)
  if [[ ! -s "$out" || "$size" -lt 1024 ]]; then
    echo "  ✗ $(basename "$s"): output missing or too small (${size}B)"; ok=0; continue
  fi
  pages=""
  command -v pdfinfo >/dev/null 2>&1 && pages=$(pdfinfo "$out" 2>/dev/null | awk '/^Pages:/{print $2}')
  if [[ -n "$pages" && "$pages" -lt 1 ]]; then
    echo "  ✗ $(basename "$s"): 0 pages"; ok=0; continue
  fi
  echo "  ✓ $(basename "$s"): ${size}B${pages:+, ${pages}p}"
done

if [[ "$tested" -eq 0 ]]; then
  echo "✗ no sample inputs found under samples/ — cannot verify candidate, keeping pinned $pinned." >&2
  exit 1
fi
if [[ "$ok" -ne 1 ]]; then
  echo "✗ candidate $latest failed smoke test — keeping pinned $pinned. Investigate / report upstream." >&2
  exit 1
fi
echo "✓ candidate $latest passed smoke test."

if [[ "$dry_run" -eq 1 ]]; then
  echo "(dry-run) would update pin $pinned → $latest and install to $dest_dir."
  exit 0
fi

# Adopt: install the verified+tested binary and bump the pin.
mkdir -p "$dest_dir"
cp "$cand" "$dest_dir/rhwp"
cp "$tmp/SHA256SUMS.txt" "$dest_dir/SHA256SUMS.txt"
chmod +x "$dest_dir/rhwp"
sed -i.bak "s/^RHWP_VERSION=\".*\"/RHWP_VERSION=\"$latest\"/" "$fetch_script" && rm -f "$fetch_script.bak"

echo "✓ updated rhwp $pinned → $latest (installed to $dest_dir, pin bumped)."
echo "  Apply to the running bot:"
echo "    launchctl kickstart -k gui/\$(id -u)/com.namun.hwp-preview-bot"
