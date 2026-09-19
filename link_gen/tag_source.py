"""
Fetches official AprilTag bitmaps from the AprilRobotics/apriltag-imgs
GitHub repo (the canonical source used by the apriltag detector library
itself) and returns them as boolean numpy arrays (True = black module).

Verified directly against the repo contents -- family folder names and
filename prefixes do NOT follow one consistent naming rule, so this
mapping is pulled from the actual repo listing rather than guessed.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass

import numpy as np
import requests
from PIL import Image

RAW_BASE = "https://raw.githubusercontent.com/AprilRobotics/apriltag-imgs/master"

# family name (as used everywhere else, e.g. --family tag36h11)
#   -> (repo folder name, filename prefix before the zero-padded id)
FAMILIES = {
    "tag16h5": ("tag16h5", "tag16_05"),
    "tag25h9": ("tag25h9", "tag25_09"),
    "tag36h11": ("tag36h11", "tag36_11"),
    "tagCircle21h7": ("tagCircle21h7", "tag21_07"),
    "tagCircle49h12": ("tagCircle49h12", "tag49_12"),
    "tagCustom48h12": ("tagCustom48h12", "tag48_12"),
    "tagStandard41h12": ("tagStandard41h12", "tag41_12"),
    "tagStandard52h13": ("tagStandard52h13", "tag52_13"),
}

DEFAULT_CACHE_DIR = pathlib.Path(".cache/tags")


class UnknownFamilyError(ValueError):
    pass


class TagFetchError(RuntimeError):
    pass


@dataclass
class TagBitmap:
    family: str
    tag_id: int
    grid: np.ndarray  # 2D bool array, True = black module, [row, col]

    @property
    def n(self) -> int:
        return self.grid.shape[0]


def fetch_tag_bitmap(family: str, tag_id: int, cache_dir: pathlib.Path | None = None) -> TagBitmap:
    """
    Download (or load from cache) the official bitmap for one tag.

    The returned grid includes the family's built-in white quiet-zone
    ring -- you do not need to add extra margin around it, it's already
    baked into every image in this repo.
    """
    if family not in FAMILIES:
        raise UnknownFamilyError(
            f"Unknown family '{family}'. Known families: {', '.join(sorted(FAMILIES))}"
        )
    folder, prefix = FAMILIES[family]
    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)

    fname = f"{prefix}_{tag_id:05d}.png"
    local_path = cache_dir / family / fname
    local_path.parent.mkdir(parents=True, exist_ok=True)

    if not local_path.exists():
        url = f"{RAW_BASE}/{folder}/{fname}"
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            raise TagFetchError(
                f"Could not fetch {url} (status {resp.status_code}). "
                f"Check that tag_id={tag_id} exists for family '{family}'."
            )
        local_path.write_bytes(resp.content)

    im = Image.open(local_path).convert("L")
    grid = np.array(im) < 128  # True where pixel is black
    return TagBitmap(family=family, tag_id=tag_id, grid=grid)


def max_known_id_hint(family: str) -> str:
    """Not authoritative -- just a pointer to check, since valid-id counts
    differ per family and aren't reflected in this repo's directory listing
    without scanning it."""
    return (
        "Family sizes vary (tag16h5 ~30 tags, tag25h9 ~35, tag36h11 ~587, "
        "tagStandard41h12 ~2115, etc). If a fetch fails with a 404, the id "
        "is probably out of range for that family -- try a smaller id."
    )
