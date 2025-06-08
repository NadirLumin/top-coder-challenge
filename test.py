import subprocess

# List of test cases: (days, miles, receipts, expected)
cases = [
    (1, 601, 497.7, 644.12),
    (4, 69, 2321.49, 322),
    (6, 825, 1692.73, 1817.77),
    (14, 1184, 2269.89, 1943.24),
    (1, 9, 2246.28, 1120.22)
]

for i, (days, miles, receipts, expected) in enumerate(cases, 1):
    print(f"\nCase {i}:")
    print(f"Expected: {expected}")
    # Call your solution.py with subprocess, capture output
    result = subprocess.run(
        ["python3", "solution.py", str(days), str(miles), str(receipts), str(expected)],
        capture_output=True, text=True
    )
    prediction = result.stdout.strip()
    print(f"Predicted: {prediction}")
    try:
        error = abs(float(prediction) - float(expected))
        print(f"Error: {error:.2f}")
    except Exception:
        print("Could not compute error (non-numeric output)")

