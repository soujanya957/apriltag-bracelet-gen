from __future__ import annotations

import argparse
import csv
import pathlib
import sys

from .geometry import CarrierProfile, load_carrier_solid, build_tag_link, export_stl
from .tag_source import fetch_tag_bitmap, FAMILIES, UnknownFamilyError, TagFetchError


def parse_ids(spec: str) -> list[int]:
    """'0-7' -> [0..7], '0,2,5' -> [0,2,5], '3' -> [3]."""
    ids: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-")
            ids.extend(range(int(lo), int(hi) + 1))
        else:
            ids.append(int(part))
    return ids


def generate(args: argparse.Namespace) -> int:
    profile = CarrierProfile.from_json(args.profile)
    carrier = load_carrier_solid(args.carrier, profile)
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ids = parse_ids(args.ids)
    manifest_path = out_dir / "manifest.csv"
    rows = []

    for tag_id in ids:
        try:
            tag = fetch_tag_bitmap(args.family, tag_id)
        except (UnknownFamilyError, TagFetchError) as e:
            print(f"[skip id {tag_id}] {e}", file=sys.stderr)
            continue

        try:
            body, insert = build_tag_link(
                carrier, profile, tag,
                tag_size_mm=args.tag_size,
                extra_length_mm=args.extra_length,
                pocket_depth_mm=args.pocket_depth,
            )
        except ValueError as e:
            print(f"[skip id {tag_id}] {e}", file=sys.stderr)
            continue

        body_path = out_dir / f"link_{args.family}_{tag_id:03d}_body.stl"
        insert_path = out_dir / f"link_{args.family}_{tag_id:03d}_insert.stl"
        export_stl(body, body_path)
        export_stl(insert, insert_path)
        print(f"id {tag_id:>4}  ->  {body_path.name}, {insert_path.name}")
        rows.append({
            "tag_id": tag_id,
            "family": args.family,
            "body_file": body_path.name,
            "insert_file": insert_path.name,
            "tag_size_mm": args.tag_size,
        })

    with manifest_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["tag_id", "family", "body_file", "insert_file", "tag_size_mm"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} link(s) to {out_dir}/  (manifest.csv included)")
    return 0


def list_families(args: argparse.Namespace) -> int:
    for name in sorted(FAMILIES):
        print(name)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="link_gen", description="Generate multicolor-printable AprilTag bracelet links.")
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="Generate one or more tag links")
    g.add_argument("--carrier", required=True, help="Path to the carrier link STEP file")
    g.add_argument("--profile", required=True, help="Path to the CarrierProfile JSON for that carrier")
    g.add_argument("--family", required=True, choices=sorted(FAMILIES), help="AprilTag family")
    g.add_argument("--ids", required=True, help="Tag id or range, e.g. '0-7' or '0,2,5'")
    g.add_argument("--tag-size", type=float, default=16.0, help="Tag footprint in mm (default 16)")
    g.add_argument("--extra-length", type=float, default=11.0, help="mm added to the spine (default 11)")
    g.add_argument("--pocket-depth", type=float, default=0.4, help="Pocket/insert depth in mm (default 0.4)")
    g.add_argument("--out-dir", default="outputs", help="Output directory")
    g.set_defaults(func=generate)

    f = sub.add_parser("families", help="List supported AprilTag families")
    f.set_defaults(func=list_families)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
