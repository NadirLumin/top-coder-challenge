
import sys
import math
import csv
import os

def calculate_reimbursement(days, miles, receipts, expected=None):
    # === Reference logic from your best-scoring script ===
    base_per_diem = 82
    base = base_per_diem * days

    mileage_component = (
        min(0.58, 0.50 + 0.08 / math.sqrt(days)) * min(miles, 200)
        + 0.23 * max(miles - 200, 0)
    )

    if receipts < 30:
        receipts_component = -20
    elif receipts < 600:
        receipts_component = receipts * 0.75
    elif receipts < 1000:
        receipts_component = 450 + math.log(receipts - 600 + 1) * 55
    else:
        receipts_component = 450 + math.log(401) * 55 + math.log(receipts - 1000 + 1) * 12

    efficiency = miles / days if days else 0
    spend_per_day = receipts / days if days else 0

    # --- Multipliers, all start at 1.0 ---
    sweet_spot_bonus = 1.0
    if 180 <= efficiency <= 220 and 4 <= days <= 6 and spend_per_day < 120:
        sweet_spot_bonus = 1.15

    long_low_penalty = 1.0
    if days > 10 and efficiency < 90 and spend_per_day < 100:
        long_low_penalty = 0.8  # or 0.75 if still overpaying
    elif 5 < days <= 10 and efficiency < 90 and spend_per_day < 100:
        long_low_penalty = 0.85

    short_high_excessive_bonus = 1.0
    if days <= 2 and efficiency >= 120 and spend_per_day >= 300:
        short_high_excessive_bonus = 1.3  # or 1.4 if still underpaying

    medium_mod_high_bonus = 1.0
    if 3 < days <= 10 and 60 < efficiency < 120 and 100 < spend_per_day < 300:
        medium_mod_high_bonus = 1.15

    extra_penalty = 1.0
    if days <= 2 and spend_per_day > 400:
        extra_penalty = 0.85  # Only for extreme cases

    cents = int(round(receipts * 100)) % 100
    rounding_bonus = 0
    if cents in [49, 99]:
        rounding_bonus = 20

    # === Compute total once, with all multipliers ===
    total = (
        (base + mileage_component + receipts_component)
        * sweet_spot_bonus
        * long_low_penalty
        * short_high_excessive_bonus
        * medium_mod_high_bonus
        * extra_penalty
        + rounding_bonus
    )

    # === CSV Logging: write bands, error, etc. for every call with expected ===
    if expected is not None:
        file_exists = os.path.isfile("errors_summary.csv")
        with open("errors_summary.csv", "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow([
                    "days","miles","receipts","expected","actual","error",
                    "per_diem","mileage","receipts_band","sweet_spot","long_low_penalty",
                    "short_high_excessive_bonus","medium_mod_high_bonus","extra_penalty",
                    "rounding_bonus","efficiency","spend_per_day"
                ])
            writer.writerow([
                days,
                miles,
                receipts,
                expected,
                total,
                total - expected,
                base,
                mileage_component,
                receipts_component,
                sweet_spot_bonus,
                long_low_penalty,
                short_high_excessive_bonus,
                medium_mod_high_bonus,
                extra_penalty,
                rounding_bonus,
                efficiency,
                spend_per_day
            ])

    # Only print diagnostics if DEBUG environment variable is set
    if expected is not None and os.environ.get("DEBUG"):
        error = abs(total - expected)
        if error > 200:
            print(f"\n🚨 High Error Case 🚨")
            print(f"Inputs: {days} days, {miles} miles, ${receipts:.2f} receipts")
            print(f"Expected: ${expected:.2f}, Got: ${total:.2f}, Error: {error:.2f}")
            if long_low_penalty != 1.0:
                print(f"[Penalty] Applied long/medium+low efficiency+low/mid spend penalty: {long_low_penalty}x")
            if short_high_excessive_bonus != 1.0:
                print(f"[Bonus] Applied very short+high efficiency+excessive spend bonus: {short_high_excessive_bonus}x")
            if medium_mod_high_bonus != 1.0:
                print(f"[Bonus] Applied medium trip+mod efficiency+high spend bonus: {medium_mod_high_bonus}x")
            if extra_penalty != 1.0:
                print(f"[Penalty] Applied excessive spend/day penalty for short trip: {extra_penalty}x")

    return round(total, 2)

if __name__ == "__main__":
    days = int(sys.argv[1])
    miles = float(sys.argv[2])
    receipts = float(sys.argv[3])
    expected = float(sys.argv[4]) if len(sys.argv) > 4 else None
    result = calculate_reimbursement(days, miles, receipts, expected=expected)
    print(result)