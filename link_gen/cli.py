from __future__ import annotations

import argparse
import csv
import os
import pathlib
import sys

from .geometry import CarrierProfile, load_carrier_solid, build_tag_link, export_stl
from .metadata import build_metadata, write_metadata
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


WRIST_DEFAULT_IDS = {"left": "0-7", "right": "20-27"}


def generate_set(args: argparse.Namespace, carrier, profile: CarrierProfile,
                 wrist: str, ids: list[int], out_dir: pathlib.Path,
                 spacer_path: pathlib.Path | None = None) -> int:
    """Generate one folder of links (one wrist). Returns number written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tag_face = args.tag_face or profile.tag_face
    rows, tags, files = [], [], {}

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
                tag_face=tag_face,
            )
        except ValueError as e:
            print(f"[skip id {tag_id}] {e}", file=sys.stderr)
            continue

        body_path = out_dir / f"link_{args.family}_{tag_id:03d}_body.stl"
        insert_path = out_dir / f"link_{args.family}_{tag_id:03d}_insert.stl"
        export_stl(body, body_path)
        export_stl(insert, insert_path)
        print(f"[{wrist}] id {tag_id:>4}  ->  {body_path.name}, {insert_path.name}")
        rows.append({
            "tag_id": tag_id,
            "family": args.family,
            "body_file": body_path.name,
            "insert_file": insert_path.name,
            "tag_size_mm": args.tag_size,
            "tag_face": tag_face,
        })
        tags.append(tag)
        files[tag_id] = (body_path.name, insert_path.name)

    with (out_dir / "manifest.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["tag_id", "family", "body_file", "insert_file", "tag_size_mm", "tag_face"])
        writer.writeheader()
        writer.writerows(rows)

    if tags:
        meta = build_metadata(
            wrist=wrist, family=args.family, tags=tags, files=files,
            tag_size_mm=args.tag_size, extra_length_mm=args.extra_length,
            pocket_depth_mm=args.pocket_depth, tag_face=tag_face,
            carrier_path=args.carrier, profile_path=args.profile, profile=profile,
            spacer_file=os.path.relpath(spacer_path, out_dir) if spacer_path else None,
        )
        write_metadata(out_dir, meta)
    print(f"Wrote {len(rows)} link(s) to {out_dir}/  (manifest.csv + metadata.json)\n")
    return len(rows)


def generate(args: argparse.Namespace) -> int:
    profile = CarrierProfile.from_json(args.profile)
    carrier = load_carrier_solid(args.carrier, profile)
    out_root = pathlib.Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    # The unmodified carrier is already loaded -- export it once as a plain
    # spacer link so the whole band can be printed from this one folder.
    spacer_path = out_root / f"spacer_{pathlib.Path(args.carrier).stem}.stl"
    export_stl(carrier, spacer_path)
    print(f"spacer  ->  {spacer_path}  (plain carrier link; print as many as the band needs)\n")

    wrists = ["left", "right"] if args.wrist == "both" else [args.wrist]
    id_specs = {"left": args.ids, "right": args.right_ids}
    for wrist in wrists:
        spec = id_specs[wrist] or WRIST_DEFAULT_IDS[wrist]
        generate_set(args, carrier, profile, wrist, parse_ids(spec), out_root / f"{wrist}_wrist", spacer_path)
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
    g.add_argument("--wrist", choices=["left", "right", "both"], default="both",
                   help="Which wrist set(s) to generate (default both). Each goes in "
                        "<out-dir>/<wrist>_wrist/ with its own manifest + metadata.json.")
    g.add_argument("--ids", default=None,
                   help="Tag ids for the left wrist (or the only wrist), e.g. '0-7' or '0,2,5'. "
                        "Default: left 0-7, right 20-27.")
    g.add_argument("--right-ids", default=None, help="Tag ids for the right wrist (default 20-27)")
    g.add_argument("--tag-size", type=float, default=16.0, help="Tag footprint in mm (default 16)")
    g.add_argument("--extra-length", type=float, default=11.0, help="mm added to the spine (default 11)")
    g.add_argument("--pocket-depth", type=float, default=0.4, help="Pocket/insert depth in mm (default 0.4)")
    g.add_argument("--tag-face", choices=["z_max", "z_min"], default=None,
                   help="Which spine face gets the tag. Default: the profile JSON's tag_face "
                        "(z_max if unset). Flip if tags come out on the wrong side.")
    g.add_argument("--out-dir", default="outputs", help="Output root; wrist subfolders go under it (default outputs)")
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
