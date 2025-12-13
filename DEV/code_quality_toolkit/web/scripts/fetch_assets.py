import os
import sys
import urllib.request
from pathlib import Path

# Configuration
ASSET_DIR = Path("web/assets")
D3_URL = "https://d3js.org/d3.v7.min.js"
D3_FILENAME = "d3.v7.min.js"

def fetch_d3():
    # 1. Create directory if it doesn't exist
    if not ASSET_DIR.exists():
        print(f"Creating directory: {ASSET_DIR}")
        ASSET_DIR.mkdir(parents=True, exist_ok=True)

    destination = ASSET_DIR / D3_FILENAME

    # 2. Check if file already exists to avoid redundant downloads
    if destination.exists():
        print(f"✔ D3.js already exists at {destination}")
        return

    # 3. Download the file
    print(f"⬇ Downloading D3.js from {D3_URL}...")
    try:
        urllib.request.urlretrieve(D3_URL, destination)
        print(f"Successfully downloaded to {destination}")
    except Exception as e:
        print(f"Error downloading asset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fetch_d3()