# Cycling Counter Workflow


## Execution order

1. `00_cycling_data_extraction.ipynb`
   - scans Transport Victoria Bicycle Volume and Speed archives;
   - extracts requested counters;
   - generates raw combined data and daily summaries.

2. `01_counter_availability_quality.ipynb`
   - verifies counter availability;
   - measures expected/observed coverage;
   - reports missing dates, continuous collection gaps, and duplicate-looking records.

3. `02_duplicate_investigation.ipynb`
   - investigates where Albert Street duplicate records originate;
   - distinguishes within-CSV, within-ZIP and across-ZIP duplication.

4. `03_duplicate_sensitivity.ipynb`
   - removes exact duplicates in a copy of the data;
   - compares original vs deduplicated daily counts and before/after results.

5. `04_preliminary_before_after_eda.ipynb`
   - performs the Albert Street observed-days-only before/after comparison;
   - produces summary tables and charts.

## Repository paths

The notebooks automatically search upward for the repository root using `.git` or `config.yaml`.

If `config.yaml` exists, the notebooks use:
- `paths.raw_dir` for the raw-data root;
- `paths.processed_dir` for the processed-data root (when available).

Default locations are:

```text
data/raw/cycling_data/
data/processed/cycling_counters/
```

Expected raw-data folders:

```text
data/raw/cycling_data/
├── bicycle_volume_speed_2019/
├── bicycle_volume_speed_2020/
├── bicycle_volume_speed_2021/
└── bicycle_volume_speed_2022/
```

A local data folder can be used without changing notebook code by setting the `CYCLING_DATA_DIR` environment variable.

## Data handling

- Raw source archives are never overwritten.
- Generated outputs are written under `data/processed/cycling_counters/`.
- Missing days are reported rather than automatically treated as zero.
- Exact duplicate removal is tested separately in a sensitivity analysis.
- Large/raw data should only be committed according to the repository's existing data-storage policy

