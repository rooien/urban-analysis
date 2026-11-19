"""
Runs SAM3 (prompt: "car") against every image in data/segment_images/ produced by
export_segment_images.py, and compares the detected count per image against the
counting team's ground truth in USIA_Merged_Parking_Counts_All_Pairs.csv (the
Final_count column -- NOT the smaller/older Final_Merged_Parking_Counts.csv).

HONESTY FLAG: the actual SAM3 call in `run_sam3_car_count()` below is a placeholder.
SAM3 is recent enough that I'm not confident of its exact current Python package name
or call signature -- verify against Meta's current SAM3 repo/docs and replace that one
function before running. Everything else here (image loading, joining to ground truth,
metrics) doesn't depend on SAM3's specific API and should be correct as-is.

Usage (after filling in run_sam3_car_count):
    python sam3_count_and_compare.py --counts "C:\\Users\\erteo\\Downloads\\USIA_Merged_Parking_Counts_All_Pairs (1).csv"
"""
import argparse
import glob
import os

import pandas as pd

IMAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "segment_images")
PROMPT = "car"


def run_sam3_car_count(image_path: str) -> int:
    """
    PLACEHOLDER -- verify against SAM3's actual current API before use.

    Expected shape: load the SAM3 model once (move that out of this per-image function
    if it's expensive), run it against `image_path` with PROMPT as the concept/text
    prompt, and return the number of detected instances (e.g. len(result.masks) or
    equivalent -- depends on SAM3's actual output object).
    """
    raise NotImplementedError(
        "Fill in the real SAM3 call here once you've checked its current API -- "
        "this repo's rules (docs/imagery_pilot_status.md) already committed to SAM3, "
        "prompt='car', benchmarked by Grattan at F1 > 94%."
    )


def load_ground_truth(counts_path: str) -> pd.DataFrame:
    df = pd.read_csv(counts_path)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--counts", required=True, help="Path to USIA_Merged_Parking_Counts_All_Pairs CSV")
    args = parser.parse_args()

    ground_truth = load_ground_truth(args.counts)

    results = []
    for image_path in sorted(glob.glob(os.path.join(IMAGE_DIR, "*.png"))):
        filename = os.path.basename(image_path)
        segment_id_str, date_str = filename.replace(".png", "").split("_", 1)
        segment_id = int(segment_id_str)
        date = pd.to_datetime(date_str)

        match = ground_truth[
            (ground_truth["Segment ID"] == segment_id) & (ground_truth["Date"] == date)
        ]
        if match.empty:
            print(f"[!] No ground truth for segment {segment_id} @ {date_str}, skipping.")
            continue

        final_count = int(match.iloc[0]["Final_count"])
        street_name = match.iloc[0]["Street Name"]
        before_after = match.iloc[0]["Before/After"]

        try:
            sam3_count = run_sam3_car_count(image_path)
        except NotImplementedError as e:
            raise SystemExit(str(e))

        error = sam3_count - final_count
        pct_error = (error / final_count * 100) if final_count else float("nan")

        results.append({
            "segment_id": segment_id,
            "street_name": street_name,
            "date": date_str,
            "before_after": before_after,
            "final_count": final_count,
            "sam3_count": sam3_count,
            "error": error,
            "pct_error": round(pct_error, 1),
        })

    if not results:
        print("No images found/matched -- run export_segment_images.py first.")
        return

    out = pd.DataFrame(results)
    out_path = os.path.join(os.path.dirname(__file__), "..", "outputs", "sam3_vs_manual_comparison.csv")
    out.to_csv(out_path, index=False)

    mae = out["error"].abs().mean()
    mean_pct_error = out["pct_error"].abs().mean()
    print(out.to_string(index=False))
    print(f"\nMAE: {mae:.2f} vehicles/image")
    print(f"Mean absolute % error: {mean_pct_error:.1f}%")
    print(f"Written to {out_path}")


if __name__ == "__main__":
    main()
