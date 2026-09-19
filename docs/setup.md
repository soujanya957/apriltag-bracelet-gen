# Setup

## Install

Python 3.10–3.12 (cadquery does not support 3.13+ yet).

```
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

or with plain pip: `pip install -r requirements.txt`. `cadquery` pulls in an
OCCT geometry kernel and takes a few minutes the first time.

Optional, only for `link_gen.verify` (decodes the generated tags with a real
detector):

```
uv pip install --python .venv/bin/python pupil-apriltags opencv-python-headless trimesh
```

## Get a carrier link

This repo does **not** bundle a carrier STEP file: bracelet/chain-link models
are usually someone else's design with its own license. Bring your own and
put it under `carriers/` (gitignored, so you won't commit it by accident).

`carriers/chainlink_v10.profile.json` is calibrated for the free
"Chain Link Bracelet" snap-link design (single roller boss + forked double
roller hinge, flat spine between them). Download that model, save it as
`carriers/chainlink_v10.step`, and you're ready to [run](run.md).

Using a different link design? See [carriers.md](carriers.md).
