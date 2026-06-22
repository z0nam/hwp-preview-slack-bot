#!/usr/bin/env bash
# fetch_rhwp.sh — download the pinned rhwp release binary for this platform,
# verify its SHA-256 against the release SHA256SUMS.txt, and install it to
# vendor/rhwp/rhwp. rhwp is the HWP/HWPX → PDF render engine this bot uses;
# it is a single self-contained binary (no Java, no LibreOffice).
#
# Usage:  scripts/fetch_rhwp.sh
# Requires: gh (GitHub CLI), tar, shasum.
set -euo pipefail

RHWP_VERSION="v0.7.17"
RHWP_REPO="edwardkim/rhwp"

repo_root=$(cd "$(dirname "$0")/.." && pwd)
dest_dir="$repo_root/vendor/rhwp"

# Map uname → release asset slug.
os=$(uname -s)
arch=$(uname -m)
case "$os/$arch" in
  Darwin/arm64)  slug="macos-aarch64";  ext="tar.gz" ;;
  Darwin/x86_64) slug="macos-x86_64";   ext="tar.gz" ;;
  Linux/x86_64)  slug="linux-x86_64";   ext="tar.gz" ;;
  *) echo "error: no prebuilt rhwp for $os/$arch (see $RHWP_REPO releases)" >&2; exit 1 ;;
esac
asset="rhwp-$RHWP_VERSION-$slug.$ext"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

echo "Downloading $asset ($RHWP_VERSION)…"
gh release download "$RHWP_VERSION" --repo "$RHWP_REPO" \
  --pattern "$asset" --pattern "SHA256SUMS.txt" --dir "$tmp" --clobber

echo "Verifying checksum…"
want=$(awk -v a="$asset" '$2==a{print $1}' "$tmp/SHA256SUMS.txt")
got=$(shasum -a 256 "$tmp/$asset" | awk '{print $1}')
if [[ -z "$want" || "$want" != "$got" ]]; then
  echo "error: checksum mismatch for $asset" >&2
  echo "  want=$want" >&2
  echo "  got =$got" >&2
  exit 1
fi
echo "  ok: $got"

echo "Extracting to ${dest_dir}…"
mkdir -p "$dest_dir"
tar xzf "$tmp/$asset" -C "$tmp"
# The tarball contains a top-level rhwp/ dir holding the binary.
cp "$tmp/rhwp/rhwp" "$dest_dir/rhwp"
cp "$tmp/SHA256SUMS.txt" "$dest_dir/SHA256SUMS.txt"
chmod +x "$dest_dir/rhwp"
xattr -d com.apple.quarantine "$dest_dir/rhwp" 2>/dev/null || true

echo "Installed: $("$dest_dir/rhwp" --version)"
