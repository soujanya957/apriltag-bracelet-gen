"""
Sanity-check generated inserts: rasterize each *_insert.stl as seen from +Z
(the printed tag face) and run a real AprilTag detector on it, confirming the
solid decodes to the id in manifest.csv.

    python3 -m link_gen.verify outputs/left_wrist

Needs `pupil-apriltags`, `opencv-python-headless`, `trimesh` (not in
requirements.txt -- they're only for this check, not for generating).
"""
from __future__ import annotations

import csv
import datetime as _dt
import json
import pathlib
import sys

import cv2
import numpy as np
import trimesh
from pupil_apriltags import Detector


def render_face(insert_path: pathlib.Path, tag_face: str = "z_max",
                px_per_mm: float = 20, margin_mm: float = 8) -> np.ndarray:
    """Black where the insert's tag-face triangles are, white elsewhere, as a
    camera facing that side would see it: from +Z x is right / y up, from -Z
    x is right / y down."""
    m = trimesh.load(insert_path)
    b = m.bounds
    x0, y0, y1 = b[0, 0] - margin_mm, b[0, 1] - margin_mm, b[1, 1] + margin_mm
    w = int((b[1, 0] - b[0, 0] + 2 * margin_mm) * px_per_mm)
    h = int((b[1, 1] - b[0, 1] + 2 * margin_mm) * px_per_mm)
    img = np.full((h, w), 255, np.uint8)
    facing = m.face_normals[:, 2] > 0.9 if tag_face == "z_max" else m.face_normals[:, 2] < -0.9
    for tri in m.triangles[facing]:
        rows = (y1 - tri[:, 1]) if tag_face == "z_max" else (tri[:, 1] - y0)
        pts = np.stack([(tri[:, 0] - x0) * px_per_mm, rows * px_per_mm], axis=1)
        cv2.fillPoly(img, [np.round(pts).astype(np.int32)], 0)
    return img


def main(out_dir: str) -> int:
    out = pathlib.Path(out_dir)
    rows = list(csv.DictReader((out / "manifest.csv").open()))
    detectors: dict[str, Detector] = {}
    bad = 0
    results = []
    for r in rows:
        fam, want = r["family"], int(r["tag_id"])
        det = detectors.setdefault(fam, Detector(families=fam))
        img = render_face(out / r["insert_file"], r.get("tag_face", "z_max"))
        got = det.detect(img)
        ids = [d.tag_id for d in got]
        ok = ids == [want]
        bad += not ok
        margin = f"margin={got[0].decision_margin:.0f}" if got else ""
        print(f"{'OK  ' if ok else 'FAIL'} {r['insert_file']}  want={want} got={ids or 'none'} {margin}")
        results.append({"id": want, "decoded_ids": ids, "ok": ok,
                        "decision_margin": round(got[0].decision_margin, 1) if got else None})
    print(f"\n{len(rows) - bad}/{len(rows)} inserts decode correctly")

    meta_path = out / "metadata.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta["verification"] = {
            "verified_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "method": "insert STL rasterized from the tag face, decoded with pupil-apriltags",
            "all_ok": bad == 0,
            "results": results,
        }
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")
        print(f"recorded in {meta_path}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "outputs"))
