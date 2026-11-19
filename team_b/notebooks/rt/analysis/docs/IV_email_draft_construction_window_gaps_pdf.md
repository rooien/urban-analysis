Subject: Data query — 26 treatment segments missing a usable construction window (quarterly panel)

We're working through the imagery-based before/after analysis for the treatment segments outside the 4 sensor-covered CBD streets (79 segments in total). To do this we need each segment's construction start/end date, which we derive from the `is_under_construction` field in `street_segment_qtr_attributes.csv` — specifically, finding the single 0→1 ("construction starts") and 1→0 ("construction ends") transition pair for each segment.

53 of the 79 segments produce a clean, unambiguous window this way. The remaining **26 do not**, for four distinct reasons. We cross-checked each of the 26 against `sites_db.csv` as well, since that file independently records intervention dates — 18 of the 26 don't appear there either (so it looks like a genuine data gap), but **8 of the 26 do have an intervention recorded in `sites_db.csv`**, which means the quarterly panel and `sites_db.csv` disagree with each other for those 8. We'd appreciate your help resolving this second group in particular, since we can't safely guess which window is correct when your own two sources don't agree.

Breakdown of the 26:

**1. Segment has zero rows in the quarterly panel at all (10 segments)**
The segment simply doesn't appear in `street_segment_qtr_attributes.csv`.

| Segment ID | Street | Suburb | In sites_db.csv? |
|---|---|---|---|
| 990 | City Road | Southbank | No |
| 1446 | Park Street | Melbourne | No |
| 1903 | Sturt Street | Southbank | No |
| 1970 | Anzac Avenue | Melbourne | No |
| 3100 | Government House Drive | Melbourne | No |
| 3125 | Kavanagh Street | Southbank | No |
| 5634 | Southbank Boulevard | Southbank | No |
| 5635 | Southbank Boulevard | Southbank | No |
| 5640 | Southbank Boulevard | Southbank | **Yes** |
| 10916 | Linlithgow Avenue | Melbourne | No |

**2. Rows exist, but `is_under_construction` is blank/unpopulated for every quarter (10 segments)**
The field was never filled in for this segment, so there's nothing to detect a transition from.

| Segment ID | Street | Suburb | In sites_db.csv? |
|---|---|---|---|
| 1587 | Armstrong St | Ballarat Central | No |
| 3503 | High Street | Wodonga | **Yes** |
| 3504 | High Street | Wodonga | No |
| 3750 | Liebig Street | Warrnambool | No |
| 3751 | Liebig Street | Warrnambool | No |
| 3752 | Liebig Street | Warrnambool | No |
| 3753 | Liebig Street | Warrnambool | No |
| 6237 | Bair St | Leongatha | No |
| 7072 | Little Bridge Street | Bakery Hill | No |
| 7851 | Main Rd | Bakery Hill | No |

**3. `is_under_construction` = 0 for every quarter — never once flagged as under construction (5 segments)**
The field is populated but never flips to 1, despite these segments having a recorded intervention.

| Segment ID | Street | Suburb | In sites_db.csv? |
|---|---|---|---|
| 859 | Rathdowne Street | Carlton | **Yes** |
| 1754 | Cecil Street | South Melbourne | **Yes** |
| 5881 | Wellington Street | Collingwood | **Yes** |
| 10530 | Swanston Street | Carlton | **Yes** |
| 10531 | Swanston Street | Carlton | **Yes** |

**4. Two separate construction cycles recorded — ambiguous which is the relevant one (1 segment)**
The panel shows two full 0→1→0 cycles rather than one, so we can't tell which corresponds to the bike-lane intervention without guessing.

| Segment ID | Street | Suburb | In sites_db.csv? |
|---|---|---|---|
| 124 | Gheringhap Street | Geelong | **Yes** |

**Segments not in `sites_db.csv` at all (18 of the 26, listed for completeness):**
City Road (990), Park Street (1446), Sturt Street (1903), Anzac Avenue (1970), Government House Drive (3100), Kavanagh Street (3125), Southbank Boulevard (5634, 5635), Linlithgow Avenue (10916), Armstrong St (1587), High Street Wodonga (3504), Liebig Street (3750, 3751, 3752, 3753), Bair St (6237), Little Bridge Street (7072), Main Rd Bakery Hill (7851).

Two specific questions:
1. For the 8 segments that **do** appear in `sites_db.csv` (859, 1754, 5881, 10530, 10531, 3503, 5640, 124) — can you confirm or correct the construction dates from your side, since the quarterly panel doesn't give us a usable window for any of them?
2. For segment 124 (Gheringhap Street) specifically — which of the two recorded construction cycles corresponds to the bike-lane intervention we're evaluating?

Happy to send over the full segment list in CSV form if that's easier to work with on your end. Let us know if you need anything else from us to track these down.
