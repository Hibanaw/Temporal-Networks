"""Write rows to results/<owner>_summary.csv (columns: dataset, metric, value, null_mean, null_std)."""
import pandas as pd

COLUMNS = ["dataset", "metric", "value", "null_mean", "null_std"]


def upsert_summary(path, rows):
    """Add rows, replacing any existing row with the same (dataset, metric)."""
    new = pd.DataFrame(rows, columns=COLUMNS)
    if path.exists():
        old = pd.read_csv(path)
        keys = set(zip(new["dataset"], new["metric"]))
        old = old[[k not in keys for k in zip(old["dataset"], old["metric"])]]
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(path, index=False)
