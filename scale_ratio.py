import csv
import os

def scale_ratio(input_path: str, output_path: str, ratio_column: str = "ratio"):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, "r", newline="", encoding="utf-8") as fin:
        reader = csv.reader(fin)
        rows = list(reader)

    if not rows:
        raise ValueError("CSV is empty")

    header = rows[0]
    try:
        ratio_idx = header.index(ratio_column)
    except ValueError:
        raise ValueError(f"Column '{ratio_column}' not found in header: {header}")

    scaled_rows = [header]
    for row in rows[1:]:
        if len(row) <= ratio_idx:
            # Skip malformed row
            continue
        val = row[ratio_idx].strip()
        if val == "":
            scaled = ""
        else:
            try:
                scaled = f"{float(val) / 100:.9f}".rstrip("0").rstrip(".")
            except ValueError:
                # Keep original if not numeric
                scaled = val
        new_row = row.copy()
        new_row[ratio_idx] = scaled
        scaled_rows.append(new_row)

    with open(output_path, "w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        writer.writerows(scaled_rows)

    print(f"Scaled ratio written to: {output_path}")

if __name__ == "__main__":
    INPUT = os.path.join("YTcomment", "YT_Final.csv")
    OUTPUT = os.path.join("YTcomment", "YT_Final_scaled.csv")
    scale_ratio(INPUT, OUTPUT)
