"""
Scans a carrier link along X to find the flat, constant-cross-section
"spine" region -- i.e. it prints the Y/Z extent of the solid at each X
slice, so you can spot the plateau where the cross-section stops
changing (that's your joint-end boundary) and read off x_cut_left,
x_cut_right, and the spine's Y/Z bounding box directly.

This is the same slicing technique used interactively to calibrate the
example chainlink_v10 profile -- packaged here so it works on any new
carrier STEP file, not just that one.
"""
from __future__ import annotations

import pathlib

import cadquery as cq
from cadquery import Solid, Vector
import numpy as np


def scan_carrier(step_path: str | pathlib.Path, solid_index: int = 0,
                  step_mm: float = 0.5, pad: float = 200.0) -> None:
    r = cq.importers.importStep(str(step_path))
    s = r.val().Solids()[solid_index]
    bb = s.BoundingBox()
    print(f"Solid {solid_index} bounding box:")
    print(f"  X: {bb.xmin:.2f} .. {bb.xmax:.2f}  (len {bb.xlen:.2f})")
    print(f"  Y: {bb.ymin:.2f} .. {bb.ymax:.2f}  (len {bb.ylen:.2f})")
    print(f"  Z: {bb.zmin:.2f} .. {bb.zmax:.2f}  (len {bb.zlen:.2f})")
    print()
    print(f"{'x':>8} {'ylen':>8} {'zlen':>8} {'ymin':>8} {'ymax':>8} {'zmin':>8} {'zmax':>8}")

    xs = np.arange(bb.xmin + step_mm / 2, bb.xmax - step_mm / 2, step_mm)
    prev_key = None
    for x in xs:
        box = Solid.makeBox(step_mm, pad, pad, Vector(x - step_mm / 2, -pad / 2, -pad / 2))
        try:
            inter = s.intersect(box)
            b2 = inter.BoundingBox()
            row = (b2.ylen, b2.zlen, b2.ymin, b2.ymax, b2.zmin, b2.zmax)
        except Exception:
            row = None
        marker = ""
        if row is not None:
            key = tuple(round(v, 1) for v in row)
            if key != prev_key:
                marker = "  <-- cross-section changes here"
            prev_key = key
        if row is None:
            print(f"{x:8.2f}   (no material)")
        else:
            print(f"{x:8.2f} {row[0]:8.2f} {row[1]:8.2f} {row[2]:8.2f} {row[3]:8.2f} "
                  f"{row[4]:8.2f} {row[5]:8.2f}{marker}")

    print()
    print("Look for a contiguous run of rows with identical ylen/zlen/ymin/ymax/zmin/zmax --")
    print("that run is your flat spine. Pick x_cut_left / x_cut_right safely inside it")
    print("(not right at the boundary row), and use that run's ymin/ymax/zmin/zmax as")
    print("spine_y_min/spine_y_max/spine_z_min/spine_z_max in your CarrierProfile JSON.")


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("step_path")
    p.add_argument("--solid-index", type=int, default=0)
    p.add_argument("--step-mm", type=float, default=0.5)
    args = p.parse_args()
    scan_carrier(args.step_path, args.solid_index, args.step_mm)


if __name__ == "__main__":
    main()
