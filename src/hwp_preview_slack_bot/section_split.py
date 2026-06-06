"""Section-split fallback for HWPX files that crash H2Orestart as a whole.

Some large HWPX documents reliably crash LibreOffice's H2Orestart import
filter when converted whole, even though every individual body section
converts fine on its own — a cumulative-content threshold bug in H2Orestart
0.7.12 (already the latest release as of 2026-05). This module splits an
.hwpx into one single-section document per body section so each can be
converted independently; the caller merges the resulting PDFs back into one.

HWPX is a ZIP (OPF) container: ``Contents/header.xml`` carries ``secCnt``,
each body section is ``Contents/sectionN.xml``, and ``Contents/content.hpf``
lists them in both a manifest (``<opf:item>``) and a spine (``<opf:itemref>``).
To keep only one section we drop the other ``sectionN.xml`` members, prune
their manifest/spine lines, and set ``secCnt`` to 1. ``mimetype`` must stay the
first member and STORED, which preserving the original member order achieves.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

_SECTION_RE = re.compile(r"Contents/section(\d+)\.xml")


def section_indices(hwpx: Path) -> list[int]:
    """Sorted body-section indices present in *hwpx* (e.g. ``[0, 1, 2]``)."""
    with zipfile.ZipFile(hwpx) as z:
        idxs = [int(m.group(1)) for n in z.namelist() if (m := _SECTION_RE.fullmatch(n))]
    return sorted(idxs)


def build_single_section(hwpx: Path, keep: int, dest: Path) -> Path:
    """Write a copy of *hwpx* to *dest* containing only body section *keep*."""
    with zipfile.ZipFile(hwpx) as z:
        names = z.namelist()
        data = {n: z.read(n) for n in names}

    removed = [
        i for n in names if (m := _SECTION_RE.fullmatch(n)) and (i := int(m.group(1))) != keep
    ]

    hpf = data["Contents/content.hpf"].decode("utf-8")
    for idx in removed:
        hpf = re.sub(r'<opf:item id="section%d"[^>]*/>' % idx, "", hpf)
        hpf = re.sub(r'<opf:itemref idref="section%d"[^>]*/>' % idx, "", hpf)
    data["Contents/content.hpf"] = hpf.encode("utf-8")

    hdr = data["Contents/header.xml"].decode("utf-8")
    hdr = re.sub(r'secCnt="\d+"', 'secCnt="1"', hdr, count=1)
    data["Contents/header.xml"] = hdr.encode("utf-8")

    drop = {"Contents/section%d.xml" % i for i in removed}
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:  # original order preserved → mimetype stays first
            if n in drop:
                continue
            ctype = zipfile.ZIP_STORED if n == "mimetype" else zipfile.ZIP_DEFLATED
            z.writestr(n, data[n], compress_type=ctype)
    return dest
