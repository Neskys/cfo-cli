"""CSV report writer (stdlib csv). Named csv_writer to avoid shadowing `csv`."""

import csv
from pathlib import Path


def write_csv(datasets, path) -> Path:
    """Write one or more datasets to a CSV file (sections separated by a blank line)."""
    path = Path(path)
    multi = len(datasets) > 1
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for i, ds in enumerate(datasets):
            if i:
                writer.writerow([])
            if multi:
                writer.writerow([f"# {ds['title']}"])
            writer.writerow(ds["headers"])
            writer.writerows(ds["rows"])
    return path
