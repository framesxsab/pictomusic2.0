"""Download the multi-language Spotify tracks dataset."""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Set your Kaggle API token via environment variable or ~/.kaggle/kaggle.json
# os.environ['KAGGLE_API_TOKEN'] = 'YOUR_TOKEN_HERE'

from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()
print("[OK] Authenticated")

import sys as _sys
_sys.path.insert(0, "src")
from config import KAGGLE_DATASET_ID

ds = KAGGLE_DATASET_ID
print(f"\n[DOWNLOAD] {ds}...")
try:
    api.dataset_download_files(ds, path="datasets", unzip=True)
    print(f"  [OK] Done")
except Exception as e:
    print(f"  [FAIL] {e}")

print("\n[DONE] Files in datasets/:")
for f in sorted(os.listdir("datasets")):
    fpath = os.path.join("datasets", f)
    if os.path.isfile(fpath):
        size_mb = os.path.getsize(fpath) / (1024*1024)
        print(f"  {f} ({size_mb:.1f} MB)")
