# Using a different carrier link

The tool assumes:

- both joint ends sit on either side of a flat "spine" along the carrier's
  local **X axis**;
- the spine's Y/Z cross-section is a plain constant prism (not tapered or
  filleted) across `[x_cut_left, x_cut_right]`.

## Calibrate a profile

```
python3 -m link_gen.profile_finder path/to/your_link.step
```

This slices the solid every 0.5 mm along X and prints the Y/Z cross-section
at each slice. Find the contiguous run where the cross-section stops
changing: that's the spine. Pick `x_cut_left` / `x_cut_right` safely inside
that run (not on a boundary row) and read `spine_y_min/max` and
`spine_z_min/max` off that row. Save as `carriers/your_link.profile.json`:

```json
{
  "x_cut_left": 0.5,
  "x_cut_right": 7.5,
  "spine_y_min": -12.0,
  "spine_y_max": 12.0,
  "spine_z_min": -6.0,
  "spine_z_max": 0.0,
  "solid_index": 0,
  "tag_face": "z_min"
}
```

`solid_index` picks which solid in the STEP file is the link, if it has
several.

## tag_face

Which spine face (`z_max` or `z_min`) ends up facing outward once the links
are snapped into a loop depends on the hinge design and is not derivable from
the STEP file. Generate and print one link; if the tag ends up on the inside,
flip `tag_face` in the profile and regenerate. `--tag-face` on the CLI
overrides it for one run. `chainlink_v10` needs `z_min`.

## How the geometry is built

1. Cut the carrier at `x_cut_left` and `x_cut_right`. Both joint ends are
   kept exactly as-is, so the result stays snap-compatible with unmodified
   links.
2. Bridge them with a new flat box, `extra_length` mm longer than the
   original spine.
3. Fetch the real bitmap for the requested family/id from
   [AprilRobotics/apriltag-imgs](https://github.com/AprilRobotics/apriltag-imgs)
   and cut a pocket into the tag face for every black module. Build a
   matching insert solid that fills those pockets flush.
