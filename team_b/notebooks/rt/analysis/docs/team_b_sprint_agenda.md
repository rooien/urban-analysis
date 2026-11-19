## Team B Sprint Meeting — Strand 2 (Imagery) Status & Sprint 3 Cross-Checks

### 1. Strand 2 status (2 min)
- Done: street selection, coverage audit (79 treatment segments checked, 53 with a clean construction window, 51 of those feasible), manual-counting rules agreed, QGIS import files generated (pilot + full-scale).
- Not done: no image exported yet, no car counted yet, SAM3 not run yet.
- Next: import pilot XML (Elizabeth St + Moorabool St, 20 images) → Ro + buddy independently count all 20 → compare → run SAM3 → validate before touching the 51-segment set.

### 2. Flag — IV data-quality issue affecting SB-302 (5 min)
- 26 of 79 treatment segments have no usable construction window in IV's quarterly panel.
- 18 don't appear in `sites_db.csv` either (genuine gap); 8 do appear in `sites_db.csv` but still conflict with the quarterly panel — IV's own two sources disagree.
- SB-302 plans to derive intervention windows from `sites_db.csv` alone — it will silently break on the same 26 segments unless it accounts for this.
- **Ask:** wait for IV's reply before finalizing SB-302's window logic, or build it to skip-and-log (not guess) on the 26, same as the imagery pipeline does.
- Evidence ready to share: `construction_window_gaps_for_IV.csv`, draft email to IV.

### 3. Flag — possible Bourke St misclassification in SB-303 (2 min)
- SB-303's corridor case studies list Bourke St as a treatment corridor.
- Coverage audit found Bourke St is a **control** street (of 10 CBD streets checked, only William/La Trobe/Peel/Exhibition are treatment).
- **Ask:** confirm before it goes into a stakeholder-facing card — is it a different Bourke St segment, or does the case study need correcting?

### 4. Open question — where does Strand 2 fit in the Sprint 3 dashboard? (3 min)
- Sprint 3's `stakeholder_metrics` / dashboard is scoped to the 17 sensor-covered segments only.
- Strand 2 covers the remaining ~79-298 segments (the majority) but has no planned path into the dashboard yet.
- **Ask:** is that intentional for this sprint's POC, or should Strand 2 output be planned in for a later sprint once SAM3 validates? Recommend: defer — stacking dashboard integration on top of unvalidated SAM3 counts repeats the scope-creep risk already flagged for the 26-segment recovery idea.

### 5. Proposed task split (3 min)
- **Ro:** owns Strand 2 end-to-end (pilot count → SAM3 validation → 51-segment scale-up decision) and stays point of contact on the IV email thread.
- **SB-302 owner:** reuse `construction_window.py`'s transition-detection logic instead of re-deriving windows from `sites_db.csv` alone — one shared source of truth for "intervention window," not two.
- **SB-303/307 owner:** hold the Bourke St entry until classification is confirmed.
- **Whole team:** decide Strand 2 → dashboard integration timing (see #4) before it's assumed into any sprint plan.

### Deferred / parked (no action needed this sprint)
26 no-window segments (cheap lookup-only pass, no classification), 219 control segments (comparison-window method undecided), bike-lane/parking buffer overlap (blocked on Bicycle Infrastructure Network dataset), 2019 sensor archive download, sensor-strand block-to-segment crosswalk.
