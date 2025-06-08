import pandas as pd

df = pd.read_csv("errors_summary.csv", on_bad_lines="skip")
print("Loaded shape:", df.shape)

def trip_type(days):
    if days <= 2:
        return "very_short"
    elif days <= 5:
        return "short"
    elif days <= 10:
        return "medium"
    else:
        return "long"

def efficiency_band(eff):
    if eff < 60:
        return "low"
    elif eff < 120:
        return "mod"
    else:
        return "high"

def spend_band(spend):
    if spend < 50:
        return "low"
    elif spend < 100:
        return "mid"
    elif spend < 300:
        return "high"
    else:
        return "excessive"

df["trip_type"] = df["days"].apply(trip_type)
df["efficiency_band"] = df["efficiency"].apply(efficiency_band)
df["spend_band"] = df["spend_per_day"].apply(spend_band)

grouped = df.groupby(["trip_type", "efficiency_band", "spend_band"]).agg(
    mean_error=("error", "mean"),
    count=("error", "count")
).reset_index()

print("Top 3 most common (by count):")
print(grouped.sort_values("count", ascending=False).head(3), "\n")

print("Top 3 bands by mean overpay (largest positive mean):")
print(grouped.sort_values("mean_error", ascending=False).head(3), "\n")

print("Top 3 bands by mean underpay (most negative mean):")
print(grouped.sort_values("mean_error").head(3), "\n")
