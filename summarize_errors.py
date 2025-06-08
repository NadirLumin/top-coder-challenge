import pandas as pd

df = pd.read_csv("errors_summary.csv", on_bad_lines="skip")
print("Loaded shape:", df.shape)

mult_cols = [
    "long_low_penalty",
    "short_high_excessive_bonus",
    "medium_mod_high_bonus",
    "extra_penalty"
]

for col in mult_cols:
    if col in df.columns:
        print(f"\nValue counts for {col}:")
        print(df[col].value_counts())
        print(f"\nMean error by {col}:")
        print(df.groupby(col)['error'].mean())
        print(f"\nNumber of cases where {col} is triggered (≠ 1.0):", df[df[col] != 1.0].shape[0])
        print(f"\nMean signed error when {col} is triggered:")
        print(df[df[col] != 1.0]['error'].mean())
        if 'trip_type' in df.columns:
            print(pd.crosstab(df[col], df['trip_type']))

# Binning (if not already present)
if 'trip_type' not in df.columns:
    df['trip_type'] = pd.cut(df['days'], bins=[0,2,5,10,100], labels=['very_short','short','medium','long'])
if 'efficiency_band' not in df.columns:
    df['efficiency_band'] = pd.cut(df['efficiency'], bins=[-1,60,180,220,350,10000], labels=['low','mod','sweet_spot','high','extreme'])
if 'spend_band' not in df.columns:
    df['spend_band'] = pd.cut(df['spend_per_day'], bins=[-1,50,100,150,400,10000], labels=['low','mid','high','excessive','very_high'])

summary = df.groupby(['trip_type','efficiency_band','spend_band'])['error'].agg(['mean','count']).reset_index()
summary = summary[summary['count'] >= 10]
print(summary.sort_values('mean', ascending=False).to_string(index=False))
