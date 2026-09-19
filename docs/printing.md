# Printing (Bambu Studio / any AMS slicer)

STL has no color. Each link is two files that share one coordinate origin:
`_body.stl` (light filament) and `_insert.stl` (black). Importing the insert
as a *part* of the body is what makes the slicer print them as one object in
two colors.

Per link:

1. **File → Import** the `_body.stl`.
2. Right-click the body in the object list → **Add part → Load...** → pick
   the matching `_insert.stl`. It lands already aligned. Do not move it.
3. Expand the object; set the body's filament to white/light grey and the
   insert part's to black.
4. If the profile's `tag_face` is `z_min` (it is for `chainlink_v10`), the tag
   is on the face that sits on the plate. Either flip the object (select →
   **F**) so the tag faces up, or print it face-down on a textured PEI plate
   for a matte tag surface. Both work; the tag face is fully planar.
5. Import `spacer_<carrier>.stl`, set the light filament, and duplicate it as
   many times as the band needs.
6. **Arrange**, slice at 0.2 mm layers (0.4 mm pocket = 2 black layers), no
   supports. Scrub to the tag layers in the preview to check the pattern.

Print one tag link first: check it snaps into a spacer with the tag facing
outward, and that a phone camera decodes it. Then run the batch.

Matte filament (matte PLA or PETG) beats glossy: glare at oblique angles is a
more common detection failure than resolution.
