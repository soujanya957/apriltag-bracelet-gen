"""
Writes a metadata.json next to each generated set of links, carrying
everything another machine needs to (a) reproduce the set and (b) detect
the printed tags: family, ids, the physical size to feed a pose estimator,
and the exact bitmaps that were cut.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import subprocess
import sys

import numpy as np

from .geometry import CarrierProfile
from .tag_source import TagBitmap

# Families OpenCV's ArUco module can decode directly (cv2.aruco.DICT_APRILTAG_*).
OPENCV_ARUCO_DICTS = {
    "tag16h5": "DICT_APRILTAG_16h5",
    "tag25h9": "DICT_APRILTAG_25h9",
    "tag36h11": "DICT_APRILTAG_36h11",
}


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return None


def black_border_ring(grid: np.ndarray) -> int:
    """Index (from the outside) of the outermost all-black ring. The tag's
    detection quad -- the square whose corners a detector returns, and whose
    side length you pass to a pose estimator -- is the outer edge of this
    ring, not the outer edge of the image (which includes the white quiet
    zone for classic families, or data bits for tagStandard*/tagCustom*)."""
    n = grid.shape[0]
    for r in range(n // 2):
        ring = np.concatenate([grid[r, r:n - r], grid[n - 1 - r, r:n - r],
                               grid[r:n - r, r], grid[r:n - r, n - 1 - r]])
        if ring.all():
            return r
    raise ValueError("no all-black border ring found in bitmap")


def build_metadata(
    *,
    wrist: str | None,
    family: str,
    tags: list[TagBitmap],
    files: dict[int, tuple[str, str]],
    tag_size_mm: float,
    extra_length_mm: float,
    pocket_depth_mm: float,
    tag_face: str,
    carrier_path: str | pathlib.Path,
    profile_path: str | pathlib.Path,
    profile: CarrierProfile,
    spacer_file: str | None = None,
) -> dict:
    n = tags[0].n
    module_mm = tag_size_mm / n
    ring = black_border_ring(tags[0].grid)
    pose_size_mm = module_mm * (n - 2 * ring)
    ids = [t.tag_id for t in tags]

    return {
        "schema": "apriltag-bracelet-gen/metadata/1",
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "generator": {
            "repo": "apriltag-bracelet-gen",
            "git_commit": _git_commit(),
            "command": "python3 -m link_gen.cli " + " ".join(sys.argv[1:]),
        },
        "wrist": wrist,
        "carrier": {
            "step_file": pathlib.Path(carrier_path).name,
            "profile_file": pathlib.Path(profile_path).name,
            "profile": profile.__dict__,
            # Unmodified carrier exported as an STL: the plain link you alternate
            # with tag links to size the band. Path is relative to this folder.
            "spacer_file": spacer_file,
        },
        "link_geometry_mm": {
            "tag_footprint": tag_size_mm,
            "module": module_mm,
            "modules_per_side": n,
            "extra_length": extra_length_mm,
            "pocket_depth": pocket_depth_mm,
            "spine_length_new": profile.spine_len + extra_length_mm,
            "tag_face": tag_face,
        },
        "detection": {
            "family": family,
            "tag_ids": ids,
            "pose_tag_size_mm": round(pose_size_mm, 4),
            "pose_tag_size_note": (
                "Side length of the black border square (outer edge), which is the "
                "quad the detector returns corners for. Pass THIS -- not the "
                f"{tag_size_mm}mm footprint -- as tag_size / markerLength for pose "
                "estimation. Measure a printed link with calipers to confirm; FDM "
                "shrinkage can change it by ~0.1mm."
            ),
            "quiet_zone_modules": ring,
            "opencv_aruco_dict": OPENCV_ARUCO_DICTS.get(family),
            "examples": {
                "pupil_apriltags": (
                    f"Detector(families='{family}').detect(gray, estimate_tag_pose=True, "
                    f"camera_params=(fx, fy, cx, cy), tag_size={pose_size_mm / 1000:.4f})  # metres"
                ),
                "apriltag_ros": {
                    "tag_family": family,
                    "standalone_tags": [{"id": i, "size": round(pose_size_mm / 1000, 4)} for i in ids],
                },
                "opencv_aruco": (
                    f"cv2.aruco.getPredefinedDictionary(cv2.aruco.{OPENCV_ARUCO_DICTS[family]}); "
                    f"markerLength={pose_size_mm / 1000:.4f}"
                    if family in OPENCV_ARUCO_DICTS else
                    "not available in OpenCV ArUco -- use the apriltag library"
                ),
            },
        },
        "tags": [
            {
                "id": t.tag_id,
                "body_file": files[t.tag_id][0],
                "insert_file": files[t.tag_id][1],
                # Row 0 = top of the tag as seen by a camera looking at the tag face.
                "bitmap": ["".join("#" if v else "." for v in row) for row in t.grid],
            }
            for t in tags
        ],
    }


def write_metadata(out_dir: pathlib.Path, meta: dict) -> pathlib.Path:
    path = out_dir / "metadata.json"
    path.write_text(json.dumps(meta, indent=2) + "\n")
    return path
