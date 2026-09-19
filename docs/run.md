# Generate links

```
python3 -m link_gen.cli generate \
  --carrier carriers/chainlink_v10.step \
  --profile carriers/chainlink_v10.profile.json \
  --family tag36h11 \
  --wrist both
```

Writes:

```
outputs/
  spacer_chainlink_v10.stl   # unmodified carrier link, once per run
  left_wrist/                # ids 0-7:   *_body.stl, *_insert.stl, manifest.csv, metadata.json
  right_wrist/               # ids 20-27: same
```

## Options

| flag | default | meaning |
|---|---|---|
| `--wrist left\|right\|both` | `both` | which set(s) to write; each goes in `<out-dir>/<wrist>_wrist/` |
| `--ids` | left `0-7` | ids for the left (or only) wrist: range `0-7`, list `0,2,5`, or one id |
| `--right-ids` | `20-27` | ids for the right wrist |
| `--tag-size` | `16` | full tag footprint in mm, quiet zone included; must fit in `spine_len + extra_length` and `spine_width` |
| `--extra-length` | `11` | mm added to the spine. Tag links are longer than plain links; alternate with spacers to size the band |
| `--pocket-depth` | `0.4` | insert thickness in mm; 0.3–0.5 for a 0.4 mm nozzle |
| `--tag-face z_max\|z_min` | from profile | which spine face gets the tag; see [carriers.md](carriers.md) |
| `--out-dir` | `outputs` | output root |

`python3 -m link_gen.cli families` lists the supported families.

## Verify

Rasterizes each insert as a camera would see the printed face and runs a real
AprilTag detector on it. Catches mirroring or module-size mistakes before you
print. Results are written into that folder's `metadata.json`.

```
python3 -m link_gen.verify outputs/left_wrist
python3 -m link_gen.verify outputs/right_wrist
```

## Choosing a family, size, and ids

- `tag36h11` is the safe default: best false-positive rejection, which
  matters when footage is processed unsupervised.
- `tag25h9` has a simpler pattern; worth trying if motion blur is the limit
  (fast wrist movement, camera close and moving).
- Keep modules ≥ ~1.2 mm on a 0.4 mm nozzle. A 10×10 family at 16 mm gives
  1.6 mm modules; below ~12 mm total you're fighting print resolution.
- Give every link a unique id and reserve a separate block per wrist
  (left 0-7, right 20-27) so one visible tag tells you which wrist it is.
