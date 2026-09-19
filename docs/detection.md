# Detecting the printed tags

Every generated folder has a `metadata.json` with what another machine needs.
The three values that matter:

| | tag36h11 at 16 mm (defaults) |
|---|---|
| **family** | `tag36h11` |
| **ids** | left wrist 0-7, right wrist 20-27 |
| **pose tag size** | **12.8 mm** — the black border square, *not* the 16 mm footprint (the outer 1.6 mm ring is white quiet zone). Confirm with calipers on a print. |

No key or code beyond that: AprilTag families are public and built into every
detector.

```python
# pupil-apriltags
from pupil_apriltags import Detector
det = Detector(families="tag36h11")
det.detect(gray, estimate_tag_pose=True, camera_params=(fx, fy, cx, cy), tag_size=0.0128)

# OpenCV ArUco (tag16h5 / tag25h9 / tag36h11 only)
d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)   # markerLength=0.0128

# apriltag_ros
# tag_family: tag36h11
# standalone_tags: [{id: 0, size: 0.0128}, ...]
```

## metadata.json fields

- `generator`: git commit and the exact command line that produced the set.
- `carrier`: the STEP name, the profile used, and `spacer_file` (relative
  path to the plain-link STL).
- `link_geometry_mm`: footprint, module size, extra length, pocket depth,
  tag face.
- `detection`: family, ids, `pose_tag_size_mm`, the OpenCV dictionary name,
  and ready-to-paste snippets for pupil-apriltags / apriltag_ros / OpenCV.
- `tags[]`: files and the exact bitmap cut for each id (row 0 = top, as a
  camera sees the tag face).
- `verification`: written by `link_gen.verify`; per-id decode result and
  decision margin.
