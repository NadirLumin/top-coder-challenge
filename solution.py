import json
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split
import joblib
import sys
import os

DATA_PATH = "public_cases.json"
MODEL_PATH = "reg_model.joblib"

def band_trip_type(days):
    if days <= 2:
        return "very_short"
    elif days <= 4:
        return "short"
    elif days <= 9:
        return "medium"
    else:
        return "long"

def band_efficiency(eff):
    if eff < 50:
        return "low"
    elif eff < 150:
        return "mod"
    elif eff < 400:
        return "high"
    else:
        return "extreme"

def band_spend(spend):
    if spend < 50:
        return "low"
    elif spend < 150:
        return "mid"
    elif spend < 300:
        return "high"
    elif spend < 600:
        return "very_high"
    else:
        return "excessive"

def load_and_prepare():
    with open(DATA_PATH) as f:
        cases = json.load(f)
    rows = []
    for row in cases:
        d = row['input']
        d['expected'] = row['expected_output']
        rows.append(d)
    df = pd.DataFrame(rows)
    df.rename(columns={
        "trip_duration_days": "days",
        "miles_traveled": "miles",
        "total_receipts_amount": "receipts"
    }, inplace=True)
    df["efficiency"] = df["miles"] / df["days"]
    df["spend_per_day"] = df["receipts"] / df["days"]
    # Band features
    df["trip_type"] = df["days"].apply(band_trip_type)
    df["efficiency_band"] = df["efficiency"].apply(band_efficiency)
    df["spend_band"] = df["spend_per_day"].apply(band_spend)
    # Encode bands
    for col in ["trip_type", "efficiency_band", "spend_band"]:
        df[col] = df[col].astype("category").cat.codes   
    # Add a trouble_band flag (can refine logic as needed)
    df["trouble_band"] = (
        (df["trip_type"] == 1) &  # short
        (df["efficiency_band"] == 0) &  # low
        (df["spend_band"].isin([3, 4]))  # very_high or excessive
    ).astype(int)
    return df

def train_and_eval(df, save_model=True):
    X = df[["days", "miles", "receipts", "efficiency", "spend_per_day", "trip_type", "efficiency_band", "spend_band", "trouble_band"]]
    y = df["expected"]
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15, random_state=42)
    reg = HistGradientBoostingRegressor()
    reg.fit(X_train, y_train)
    val_preds = reg.predict(X_val)
    val_mae = abs(val_preds - y_val).mean()
    print(f"Validation Mean Absolute Error: {val_mae:.2f}")
    if save_model:
        joblib.dump(reg, MODEL_PATH)
        print(f"Model saved to: {MODEL_PATH}")
    return reg

def cli_predict():
    if not os.path.isfile(MODEL_PATH):
        print("Model not found. Please run this script without CLI arguments to train and save the model first.")
        sys.exit(1)
    reg = joblib.load(MODEL_PATH)
    if len(sys.argv) < 4:
        print("Usage: python this_script.py days miles receipts [expected]")
        sys.exit(1)
    days = float(sys.argv[1])
    miles = float(sys.argv[2])
    receipts = float(sys.argv[3])
    efficiency = miles / days if days else 0
    spend_per_day = receipts / days if days else 0
    trip_type = band_trip_type(days)
    efficiency_band = band_efficiency(efficiency)
    spend_band = band_spend(spend_per_day)
    band_maps = {
        "trip_type": {"very_short":0, "short":1, "medium":2, "long":3},
        "efficiency_band": {"low":0, "mod":1, "high":2, "extreme":3},
        "spend_band": {"low":0, "mid":1, "high":2, "very_high":3, "excessive":4}
    }
    # Compute trouble_band for this input
    trouble_band = int(
        (band_maps["trip_type"][trip_type] == 1) and
        (band_maps["efficiency_band"][efficiency_band] == 0) and
        (band_maps["spend_band"][spend_band] in [3, 4])
    )
    X = pd.DataFrame([{
        "days": days,
        "miles": miles,
        "receipts": receipts,
        "efficiency": efficiency,
        "spend_per_day": spend_per_day,
        "trip_type": band_maps["trip_type"][trip_type],
        "efficiency_band": band_maps["efficiency_band"][efficiency_band],
        "spend_band": band_maps["spend_band"][spend_band],
        "trouble_band": trouble_band
    }])
    pred = reg.predict(X)[0]
    # Optional: cap prediction for trouble_band cases (e.g., 50% of receipts)
    if trouble_band == 1:
        pred = min(pred, receipts * 0.5)
    print(round(pred, 2))
    # Only print error in debug mode, not when called from eval.sh/run.sh
    if len(sys.argv) > 4 and os.environ.get("DEBUG_PREDICT") == "1":
        expected = float(sys.argv[4])
        print(f"Error: {round(pred-expected, 2)}")

def batch_eval(write_csv=True):
    df = load_and_prepare()
    if not os.path.isfile(MODEL_PATH):
        print("Model not found. Train it first by running with no CLI args.")
        sys.exit(1)
    reg = joblib.load(MODEL_PATH)
    X = df[["days", "miles", "receipts", "efficiency", "spend_per_day", "trip_type", "efficiency_band", "spend_band", "trouble_band"]]
    preds = reg.predict(X)
    df['predicted'] = preds
    df['error'] = abs(df['predicted'] - df['expected'])
    df['signed_error'] = df['predicted'] - df['expected']
    if write_csv:
        df_out = df.copy()
        df_out['case_num'] = range(1, len(df) + 1)
        df_out[['case_num','days','miles','receipts','expected','predicted','error','signed_error','efficiency','spend_per_day']].to_csv('errors_summary.csv', index=False)
        print("Written to errors_summary.csv for further inspection.\n")
    mean_error = df['error'].mean()
    median_error = df['error'].median()
    max_error = df['error'].max()
    min_error = df['error'].min()
    num_cases = len(df)
    exact_matches = (df['error'] < 0.01).sum()
    close_matches = (df['error'] < 1.0).sum()
    exact_pct = 100 * exact_matches / num_cases
    close_pct = 100 * close_matches / num_cases
    score = mean_error * 100 + (num_cases - exact_matches) * 0.1
    print(f"\n✅ Evaluation Complete!")
    print(f"\n📈 Results Summary:")
    print(f"  Total test cases: {num_cases}")
    print(f"  Exact matches (±$0.01): {exact_matches} ({exact_pct:.1f}%)")
    print(f"  Close matches (±$1.00): {close_matches} ({close_pct:.1f}%)")
    print(f"  Mean Absolute Error: ${mean_error:.2f}")
    print(f"  Median Error: ${median_error:.2f}")
    print(f"  Maximum Error: ${max_error:.2f}")
    print(f"\n🎯 Your Score: {score:.2f} (lower is better)\n")
    print("Top 5 High-Error Cases:")
    print(df.assign(case_num=range(1, num_cases+1)).sort_values('error', ascending=False)
             .head(5)[['case_num','days','miles','receipts','expected','predicted','error']].to_string(index=False))

if __name__ == "__main__":
    if "--batch-eval" in sys.argv:
        batch_eval()
    elif len(sys.argv) >= 4:
        cli_predict()
    else:
        print("No CLI args: Training model on public_cases.json ...")
        df = load_and_prepare()
        reg = train_and_eval(df)
        print("Done. You can now run predictions via CLI args: days miles receipts [expected] or --batch-eval")