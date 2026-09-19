"""
Turns a "carrier" bracelet link (any snap/hinge link design, given as a
STEP file) into a multicolor-printable AprilTag link, by:

  1. Cutting the carrier at two X planes that bound a flat, constant
     cross-section "spine" region between its two joint ends.
  2. Replacing that spine with a longer flat box (so there's room for a
     tag), while leaving both original joint ends completely untouched
     -- this is what keeps the result snap-compatible with your other,
     unmodified links.
  3. Cutting shallow pockets into the new spine's top face everywhere
     the tag bitmap is black, and building a matching "insert" solid
     that plugs those pockets flush.

You print `body` in one filament color and `insert` in another (Bambu
Studio: load both STLs, Add Part the insert onto the body, assign
filament colors per-part -- they already share the same coordinate
origin, so no repositioning is needed).

IMPORTANT ASSUMPTIONS (see profile_finder.py to check these for a new
carrier):
  - The two joint ends sit on either side of the spine along the
    carrier's local X axis.
  - The spine's cross-section (Y and Z extent) is constant across the
    whole [x_cut_left, x_cut_right] range -- i.e. it's a plain prism,
    not tapered or filleted. profile_finder.py's `scan` command will
    show you this directly for your file.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

import cadquery as cq
from cadquery import Solid, Vector
import numpy as np

from .tag_source import TagBitmap


@dataclass
class CarrierProfile:
    """Geometric calibration for one carrier link design.  Create one of
    these per bracelet/link model you want to use -- see
    profile_finder.py to help measure x_cut_left / x_cut_right for a
    new STEP file, and just read the Y/Z bounding box of the flat
    region for the rest.
    """
    x_cut_left: float     # end of the left joint end / start of flat spine
    x_cut_right: float    # start of the right joint end / end of flat spine
    spine_y_min: float
    spine_y_max: float
    spine_z_min: float
    spine_z_max: float    # top of the spine -- tag pockets are cut down from here
    solid_index: int = 0  # which Solids()[i] in the STEP file is the link

    @classmethod
    def from_json(cls, path: str | pathlib.Path) -> "CarrierProfile":
        data = json.loads(pathlib.Path(path).read_text())
        return cls(**data)

    def to_json(self, path: str | pathlib.Path) -> None:
        pathlib.Path(path).write_text(json.dumps(self.__dict__, indent=2))

    @property
    def spine_len(self) -> float:
        return self.x_cut_right - self.x_cut_left

    @property
    def spine_width(self) -> float:  # Y extent
        return self.spine_y_max - self.spine_y_min

    @property
    def spine_thickness(self) -> float:  # Z extent
        return self.spine_z_max - self.spine_z_min


def load_carrier_solid(step_path: str | pathlib.Path, profile: CarrierProfile) -> cq.Solid:
    r = cq.importers.importStep(str(step_path))
    solids = r.val().Solids()
    return solids[profile.solid_index]


def _half_space(xmin: float, xmax: float, pad: float = 200.0) -> Solid:
    return Solid.makeBox(xmax - xmin, pad, pad, Vector(xmin, -pad / 2, -pad / 2))


def _fuse_all(solids: list[Solid]) -> Solid:
    out = solids[0]
    for s in solids[1:]:
        out = out.fuse(s)
    return out


def build_tag_link(
    carrier: Solid,
    profile: CarrierProfile,
    tag: TagBitmap,
    tag_size_mm: float,
    extra_length_mm: float,
    pocket_depth_mm: float = 0.4,
) -> tuple[Solid, Solid]:
    """
    Returns (body_solid, insert_solid).

    tag_size_mm is the full footprint of the tag bitmap (including its
    built-in white quiet zone) -- it must fit within
    profile.spine_len + extra_length_mm, and within profile.spine_width,
    or this raises ValueError.
    """
    new_spine_len = profile.spine_len + extra_length_mm
    if tag_size_mm > new_spine_len or tag_size_mm > profile.spine_width:
        raise ValueError(
            f"tag_size_mm={tag_size_mm} doesn't fit the spine "
            f"({new_spine_len:.1f} x {profile.spine_width:.1f} mm available). "
            f"Increase extra_length_mm or shrink the tag."
        )

    left_piece = carrier.intersect(_half_space(-200, profile.x_cut_left))
    right_piece = carrier.intersect(_half_space(profile.x_cut_right, 200))
    right_piece = right_piece.translate((extra_length_mm, 0, 0))

    spine_box = Solid.makeBox(
        new_spine_len,
        profile.spine_width,
        profile.spine_thickness,
        Vector(profile.x_cut_left, profile.spine_y_min, profile.spine_z_min),
    )

    body = left_piece.fuse(spine_box).fuse(right_piece).clean()

    grid = tag.grid
    n = grid.shape[0]
    module = tag_size_mm / n

    spine_center_x = profile.x_cut_left + new_spine_len / 2.0
    x0 = spine_center_x - tag_size_mm / 2.0
    y0 = -tag_size_mm / 2.0
    z_top = profile.spine_z_max

    pocket_boxes, insert_boxes = [], []
    for row in range(n):
        for col in range(n):
            if not grid[row, col]:
                continue
            px = x0 + col * module
            py = y0 + row * module
            pocket_boxes.append(
                Solid.makeBox(module, module, pocket_depth_mm + 0.02,
                               Vector(px, py, z_top - pocket_depth_mm - 0.01))
            )
            insert_boxes.append(
                Solid.makeBox(module, module, pocket_depth_mm,
                               Vector(px, py, z_top - pocket_depth_mm))
            )

    if not pocket_boxes:
        raise ValueError("Tag bitmap has no black modules -- check the fetched bitmap.")

    body_with_pockets = body.cut(_fuse_all(pocket_boxes)).clean()
    insert = _fuse_all(insert_boxes).clean()
    return body_with_pockets, insert


def export_stl(solid: Solid, path: str | pathlib.Path) -> None:
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(cq.Workplane(obj=solid), str(path))
