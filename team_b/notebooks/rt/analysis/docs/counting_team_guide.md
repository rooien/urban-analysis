# Imagery Counting Guide — Loading Images & Manual Counting

**For:** the 10-person counting team (5 pairs), full-scale set (51 segments, 678 images)
**Before you start:** each pair should have received their two matching files —
`qgis_xyz_connections_pair{N}_A.xml` and `qgis_xyz_connections_pair{N}_B.xml` (same
content, one copy each so you can both work independently in your own QGIS session).

---

## Part 1 — Load your XML into QGIS

1. **Get your API key into the file first.** Open your assigned `.xml` file in a text
   editor (Notepad is fine) and Find & Replace `YOUR_API_KEY` with your real Nearmap key
   — *only in your own local copy, never commit this back to git.* If your file already
   has a key filled in, you can skip this.
2. In QGIS: **Layer → Data Source Manager → XYZ Tiles → Load Connections**, then select
   your `.xml` file. Every image in your set will appear as a saved XYZ connection —
   these load as individual dated map layers, not one combined layer.
3. Confirm the connections loaded: check the browser panel under "XYZ Tiles" — you
   should see one entry per image, named `{street_segment_id}_{street}_{before/after}_{date}`.

## Part 2 — Zoom to the correct segment

4. Open `street_spatial_study_area.gpkg` and load the **`buffered_full`** layer — this
   holds a pre-built buffer polygon per segment.
5. Filter it to your segment: right-click the layer → **Filter**, and set
   `"street_segment_id" = <your segment ID>` (or use Select Features and search).
6. Zoom to the selected feature (right-click → **Zoom to Selection**, or the toolbar
   equivalent). This gives you the correct extent for that segment before you export
   anything — don't eyeball the zoom level manually, the buffer defines it.

## Part 3 — Export each image

7. **Hide every vector layer** (street segments, buffer, sensor points, etc.) — only
   the imagery tile layer should be visible on screen when you export.
8. Turn on **only the one dated XYZ layer** you're exporting right now, and turn off
   every other date for that segment. If two dates are visible at once you will export
   the wrong (or a blended) image without realizing it — check this every single time,
   it's the easiest step to get wrong.
9. **Project → Import/Export → Export Map to Image.**
   - **Tick "Save world file"** — without this the image loses its georeferencing and
     is useless for measurement.
   - **Set resolution to approximately 7 cm/pixel — don't just type a DPI number.**
     A fixed DPI gives a different ground resolution on every segment, since each
     buffer extent is a different size. Instead:
     1. **Check the project CRS is EPSG:7899 (Vicgrid)** — CRS indicator bottom-right
        of the QGIS window. The Nearmap tile layer itself stays EPSG:3857 as served
        (never override that), but the *project* CRS must be 7899 for the Extent
        numbers below to be true ground metres — in 3857 they'd be distorted.
     2. In the dialog's Extent group, read the extent width: `X Max - X Min` (metres).
     3. Compute `width_px = round(extent_width_m / 0.07)` and type that into the
        **Width** field, with the aspect-ratio lock (chain icon) **on** so Height
        auto-scales. Ignore the DPI field — it updates itself.
     4. Before confirming export, check `extent_width_m / width_px` (shown in the
        dialog) comes out close to 0.07 m — that's your actual ground resolution.
     5. **You only need to do this calculation once per segment, not once per
        image.** Every date/image for the same segment shares the same extent, so
        the Width you computed here carries over — see the note on step 11 below.
   - **Filename convention:** `{street_segment_id}_{capture_date}.tif`, e.g.
     `9168_2020-02-17.tif`. Keep this exact — the SAM3 validation step later depends on
     consistent naming.
10. **Reopen the exported .tif** and confirm it's correctly georeferenced (drag it back
    into QGIS, check it lines up with the buffer/street layer) **before moving on to the
    next image.** Catching a bad export immediately is much cheaper than finding it
    after all your images are done.
11. **Repeat, but note this splits into two loops, not one:**
    - **Per segment** (whenever `street_segment_id` changes): redo step 6 (zoom to
      selection) and the resolution calc in step 9 (new extent → new Width in
      pixels).
    - **Per image** (every date within that same segment): skip the re-zoom and
      the resolution calc — just redo steps 7–8 (hide vectors, toggle to the one
      correct dated layer) and step 9's export itself (Width field should already
      hold the value you computed for this segment — glance at it to confirm
      before exporting, don't retype it), then step 10 (reopen and verify
      georeferencing).

    With ~13 images per segment on average, this means the resolution math only
    happens a handful of times across your whole set, not once per image.

**One thing worth checking before you start:** the shared QGIS project already has a
layer called `Counting_9168_19/08/31`, which suggests some counting may have already
been attempted on segment 9168. Check with Ro before re-doing that one from scratch.

---

## Part 4 — What to count, and what to watch for

Apply these rules identically on every image — consistency matters more than any
individual judgment call, since the whole point is comparing your count against your
partner's.

- **Count any stationary vehicle in the kerbside lane** as occupying a space. Exclude
  driveways, clearways, loading/bus zones, and moving traffic.
- **Cropped/edge vehicles:** count it in whichever image tile contains its visual
  center — don't double-count a vehicle that straddles two tiles, and don't drop one
  that's mostly off-frame if its center is in your tile.
- **Obscured by trees or shadow:** if less than 15% of a kerb stretch is visible in the
  image, exclude that stretch and note it (Grattan's threshold) — don't guess what's
  underneath.
- **Capacity is measured per-image, not once per segment.** Kerb length ÷ 6.0 m
  (parallel parking) or ÷ 2.5 m (angle parking), round down, minus 18% where a run over
  15 m has driveways. Because a bike lane changes available kerb length between before
  and after, you must re-measure capacity on every single image — don't reuse a number
  from an earlier date on the same street.
- **Count all vehicle types** — cars, vans, trucks, everything. SAM3 (the automated
  validation step) only detects "car," so if your manual count is higher than SAM3's on
  a van-heavy street, that's an expected, already-known discrepancy — not a sign your
  count is wrong.

**Log your count per image**, not just a segment total — you'll need the per-image
number to compare against your partner's and against SAM3 later. Use whatever sheet
format Ro shares, but keep segment ID, date, before/after, and your count all on one row
per image.

**When you and your partner disagree on a count:** don't just average it or pick one —
write down *why* you disagree (missed vehicle, obscured spot, different call on a
cropped vehicle, etc.). That's the signal that tells us whether the rules themselves
need tightening, which is the actual purpose of the full-overlap approach.

---

**Questions or an image that won't export cleanly?** Flag it to Ro rather than guessing
— a wrong georeference or a missed date-toggle is easy to miss until much later.
