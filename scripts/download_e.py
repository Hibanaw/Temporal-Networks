"""Download the raw PS and CM files used by member E (and by C and D).

  data/raw/primaryschool/primaryschool.csv.gz        SocioPatterns, CC BY-NC-SA 4.0
  data/raw/primaryschool/primaryschool_metadata.txt
  data/raw/collegemsg/CollegeMsg.txt.gz              SNAP

Usage: python scripts/download_e.py
"""
import hashlib
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
FILES = [
    ("https://www.sociopatterns.org/assets/data/primaryschool.csv.gz",
     RAW / "primaryschool" / "primaryschool.csv.gz"),
    ("https://www.sociopatterns.org/assets/data/primaryschool_metadata.txt",
     RAW / "primaryschool" / "primaryschool_metadata.txt"),
    ("https://snap.stanford.edu/data/CollegeMsg.txt.gz",
     RAW / "collegemsg" / "CollegeMsg.txt.gz"),
]


def main():
    for url, path in FILES:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            urllib.request.urlretrieve(url, path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"{path.relative_to(RAW.parents[1])}  {path.stat().st_size} bytes  sha256 {digest}")


if __name__ == "__main__":
    main()
