# apriltag-bracelet-gen

Multicolor-printable AprilTag links for a snap-together bracelet. Takes any
chain-link design (as a STEP file), stretches its flat spine to fit a real
AprilTag, and outputs a body STL (light filament) plus an insert STL (black)
per link. The joint ends are left untouched, so tag links snap into the
original, unmodified links.

Built for wrist-worn fiducial tracking (anchoring egocentric-video hand pose
to a known frame for imitation-learning data), but nothing here is specific
to that.

![tag link next to an unmodified spacer link, seen from the tag face](examples/preview_tag_face.png)

*Left: generated tag link (tag36h11 id 0), light body with the black insert
flush in its pockets. Right: the unmodified carrier, exported as the spacer.*

## Quick start

```
uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -r requirements.txt
python3 -m link_gen.cli generate --carrier carriers/chainlink_v10.step \
  --profile carriers/chainlink_v10.profile.json --family tag36h11 --wrist both
```

## Docs

- [Setup](docs/setup.md) — install, get a carrier link
- [Run](docs/run.md) — generate, options, verify, choosing family/size/ids
- [Printing](docs/printing.md) — Bambu Studio multicolor workflow
- [Detection](docs/detection.md) — family, ids, pose size, `metadata.json`
- [Carriers](docs/carriers.md) — calibrate a profile for a different link design

`examples/` has one finished link (id 0 body + insert) and its metadata, to
try the print workflow without installing anything.

## Layout

```
link_gen/
  cli.py              generate / families commands
  geometry.py         CarrierProfile + cut/stretch/pocket CAD logic
  tag_source.py       fetches + caches official AprilTag bitmaps
  metadata.py         writes metadata.json per generated set
  verify.py           decodes generated inserts with a real detector
  profile_finder.py   scans a new carrier STEP to calibrate a profile
carriers/
  *.profile.json      calibration per carrier (committed)
  *.step              your carrier files (gitignored)
docs/                 guides linked above
examples/             one generated link + preview image
outputs/              generated sets (gitignored)
```
